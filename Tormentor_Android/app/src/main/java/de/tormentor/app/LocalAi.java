package de.tormentor.app;

import org.json.*;
import java.io.*;
import java.net.*;
import java.nio.charset.StandardCharsets;

final class LocalAi {
    private volatile HttpURLConnection active;
    private volatile boolean cancelled;
    static String address(String value) throws IOException {
        try {
            URI uri=new URI(value.trim());String host=uri.getHost();
            if(!"http".equals(uri.getScheme())||host==null||uri.getUserInfo()!=null||uri.getQuery()!=null||uri.getFragment()!=null||!(uri.getPath().isEmpty()||uri.getPath().equals("/")))throw new IOException("Bitte http://Laptop-IP:8765 verwenden.");
            String[] parts=host.split("\\.");if(parts.length!=4)throw new IOException("Bitte die IPv4-Adresse des Laptops verwenden.");int[] ip=new int[4];for(int i=0;i<4;i++){ip[i]=Integer.parseInt(parts[i]);if(ip[i]<0||ip[i]>255)throw new IOException("Ungültige IP-Adresse");}
            if(!(ip[0]==10||(ip[0]==192&&ip[1]==168)||(ip[0]==172&&ip[1]>=16&&ip[1]<=31)))throw new IOException("Bitte eine Adresse aus deinem privaten WLAN verwenden.");
            int port=uri.getPort()<0?8765:uri.getPort();if(port<1||port>65535)throw new IOException("Ungültiger Port");return "http://"+host+":"+port;
        }catch(URISyntaxException|NumberFormatException e){throw new IOException("Ungültige Laptop-Adresse");}
    }
    void cancel(){cancelled=true;HttpURLConnection c=active;if(c!=null)c.disconnect();}
    JSONObject ask(String host,String token,String question,boolean test) throws Exception {
        String endpoint=address(host)+(test?"/test":"/ask");if(cancelled)throw new IOException("Abgebrochen");
        HttpURLConnection c=(HttpURLConnection)new URL(endpoint).openConnection();active=c;
        try {
            c.setConnectTimeout(10000);c.setReadTimeout(240000);c.setInstanceFollowRedirects(false);c.setRequestMethod("POST");c.setDoOutput(true);c.setRequestProperty("Content-Type","application/json");c.setRequestProperty("X-Tormentor-Token",token);
            byte[] payload=new JSONObject().put("question",question).toString().getBytes(StandardCharsets.UTF_8);c.setFixedLengthStreamingMode(payload.length);
            try(OutputStream out=c.getOutputStream()){out.write(payload);}
            int code=c.getResponseCode();InputStream source=code>=200&&code<300?c.getInputStream():c.getErrorStream();if(source==null)throw new IOException("Laptop antwortet mit HTTP "+code);
            try(InputStream in=source;ByteArrayOutputStream result=new ByteArrayOutputStream()){byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))!=-1){if(cancelled)throw new IOException("Abgebrochen");if(result.size()+n>16*1024*1024)throw new IOException("Antwort zu groß");result.write(buffer,0,n);}JSONObject data=new JSONObject(result.toString("UTF-8"));if(code<200||code>=300)throw new IOException(data.optString("error","Laptop antwortet mit HTTP "+code));if(data.optString("text").trim().isEmpty())throw new IOException("Leere Antwort vom Laptop");return data;}
        } finally {c.disconnect();if(active==c)active=null;}
    }
}
