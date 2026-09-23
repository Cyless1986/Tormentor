package de.tormentor.app;

import java.io.*;
import java.net.*;
import java.security.MessageDigest;
import org.json.JSONObject;

final class LoreTransfer {
    private volatile HttpURLConnection active;
    private volatile boolean cancelled;
    void cancel(){cancelled=true;HttpURLConnection connection=active;if(connection!=null)connection.disconnect();}
    JSONObject send(String host,String token,File audio,String title)throws Exception{
        long size=audio.length();
        if(size<1||size>1024L*1024*1024)throw new IOException("Aufnahmen können bis zu 1 GB groß sein.");
        MessageDigest digest=MessageDigest.getInstance("SHA-256");
        byte[] buffer=new byte[65536];
        try(InputStream input=new FileInputStream(audio)){int n;while((n=input.read(buffer))!=-1){if(cancelled)throw new IOException("Übertragung abgebrochen.");digest.update(buffer,0,n);}}
        StringBuilder checksum=new StringBuilder();for(byte value:digest.digest())checksum.append(String.format(java.util.Locale.ROOT,"%02x",value&255));
        String name=audio.getName();String extension=name.substring(name.lastIndexOf('.')).toLowerCase(java.util.Locale.ROOT);
        HttpURLConnection connection=(HttpURLConnection)new URL(LocalAi.address(host)+"/lore/audio").openConnection();active=connection;
        try{
            connection.setConnectTimeout(10000);connection.setReadTimeout(120000);connection.setInstanceFollowRedirects(false);
            connection.setRequestMethod("POST");connection.setDoOutput(true);connection.setFixedLengthStreamingMode(size);
            connection.setRequestProperty("Content-Type","application/octet-stream");
            connection.setRequestProperty("X-Tormentor-Token",token);
            connection.setRequestProperty("X-Tormentor-SHA256",checksum.toString());
            connection.setRequestProperty("X-Tormentor-Audio-Extension",extension);
            connection.setRequestProperty("X-Tormentor-Title",URLEncoder.encode(title,"UTF-8").replace("+","%20"));
            if(cancelled)throw new IOException("Übertragung abgebrochen.");
            try(InputStream input=new FileInputStream(audio);OutputStream output=connection.getOutputStream()){
                int n;while((n=input.read(buffer))!=-1){if(cancelled)throw new IOException("Übertragung abgebrochen.");output.write(buffer,0,n);}
            }
            int code=connection.getResponseCode();InputStream source=code>=200&&code<300?connection.getInputStream():connection.getErrorStream();
            if(source==null)throw new IOException("Laptop antwortet mit HTTP "+code);
            try(InputStream input=source;ByteArrayOutputStream output=new ByteArrayOutputStream()){
                int n;while((n=input.read(buffer))!=-1){if(output.size()+n>16000)throw new IOException("Antwort zu groß.");output.write(buffer,0,n);}
                JSONObject response=new JSONObject(output.toString("UTF-8"));
                if(code<200||code>=300)throw new IOException(response.optString("error","Übertragung fehlgeschlagen."));
                return response;
            }
        }finally{connection.disconnect();active=null;}
    }
}
