package de.tormentor.app;

import android.content.Context;
import android.net.Uri;
import android.database.Cursor;
import android.provider.OpenableColumns;
import android.util.AtomicFile;
import org.json.*;
import java.io.*;
import java.util.*;

/** App-owned copies. Never deletes or writes the original document selected by the user. */
final class Library {
    final Context context;
    final File media;
    final AtomicFile index;
    final ArrayList<Scene> scenes = new ArrayList<>();
    static final class Item {
        final String id, name, kind;
        Item(String id, String name, String kind) { this.id=id; this.name=name; this.kind=kind; }
        JSONObject json() throws JSONException { return new JSONObject().put("id",id).put("name",name).put("kind",kind); }
    }
    static final class Scene {
        final String id;
        String name;
        String voiceName;
        final ArrayList<Item> items = new ArrayList<>();
        Scene(String id, String name) { this.id=id; this.name=name;this.voiceName=name.equalsIgnoreCase("Dungeon")?"Verlies":name; }
    }
    Library(Context context) throws Exception {
        this.context=context;
        media=new File(context.getFilesDir(),"media");
        if (!media.isDirectory() && !media.mkdirs()) throw new IOException("Medienspeicher nicht verfügbar");
        index=new AtomicFile(new File(context.getFilesDir(),"library.json"));
        if (index.getBaseFile().exists() || new File(index.getBaseFile()+".bak").exists()) {
            String data=new String(index.readFully(), java.nio.charset.StandardCharsets.UTF_8);
            JSONArray array=new JSONObject(data).getJSONArray("scenes");
            for(int i=0;i<array.length();i++) {
                JSONObject obj=array.getJSONObject(i);
                Scene scene=new Scene(obj.getString("id"), obj.getString("name"));
                scene.voiceName=obj.optString("voiceName",scene.voiceName);
                JSONArray items=obj.getJSONArray("items");
                for(int j=0;j<items.length();j++) {
                    JSONObject item=items.getJSONObject(j);
                    String id=item.getString("id");
                    if (!id.matches("[a-zA-Z0-9._-]+")) throw new IOException("Ungültiger Medieneintrag");
                    scene.items.add(new Item(id,item.getString("name"),item.getString("kind")));
                }
                scenes.add(scene);
            }
        } else {
            for(String name:new String[]{"Rätsel","Taverne","Dungeon","Wald","Höhle","Bosskampf"})
                scenes.add(new Scene(UUID.randomUUID().toString(),name));
            save();
        }
    }
    synchronized void save() throws Exception {
        JSONArray array=new JSONArray();
        for(Scene scene:scenes) {
            JSONArray items=new JSONArray();
            for(Item item:scene.items) items.put(item.json());
            array.put(new JSONObject().put("id",scene.id).put("name",scene.name).put("voiceName",scene.voiceName).put("items",items));
        }
        byte[] bytes=new JSONObject().put("version",1).put("scenes",array).toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8);
        FileOutputStream out=null;
        try { out=index.startWrite(); out.write(bytes); index.finishWrite(out); }
        catch(Exception e) { if(out!=null) index.failWrite(out); throw e; }
    }
    File file(Item item) { return new File(media,item.id); }
    String name(Uri uri) {
        try(Cursor cursor=context.getContentResolver().query(uri,new String[]{OpenableColumns.DISPLAY_NAME},null,null,null)) {
            if(cursor!=null && cursor.moveToFirst()) return cursor.getString(0);
        } catch(Exception ignored) { }
        return "Importierte Datei";
    }
    static String kind(String name, String mime) throws IOException {
        String n=name.toLowerCase(Locale.ROOT);
        if(n.matches(".*\\.(mp3|wav|ogg|m4a|aac|flac)$") || (mime!=null && mime.startsWith("audio/"))) return "audio";
        if(n.endsWith(".mp4") || "video/mp4".equals(mime)) return "video";
        if(n.matches(".*\\.(png|jpg|jpeg|webp)$") || (mime!=null && mime.startsWith("image/"))) return "image";
        throw new IOException("Dateiformat nicht unterstützt: "+name);
    }
    Item copy(InputStream source,String name,String kind) throws IOException {
        String extension=kind.equals("video")?".mp4":kind.equals("image")?".img":".audio";
        Item item=new Item(UUID.randomUUID()+extension,name,kind);
        File target=file(item);
        try(FileOutputStream out=new FileOutputStream(target)) {
            byte[] buffer=new byte[128*1024]; int read;
            while((read=source.read(buffer))!=-1) out.write(buffer,0,read);
            out.getFD().sync();
        } catch(IOException e) { target.delete(); throw e; }
        return item;
    }
    synchronized void add(Scene scene,Item item) throws Exception {
        scene.items.add(item);
        try { save(); } catch(Exception e) { scene.items.remove(item); file(item).delete(); throw e; }
    }
    synchronized void remove(Scene scene,Item item) throws Exception {
        int pos=scene.items.indexOf(item); scene.items.remove(item);
        try { save(); } catch(Exception e) { scene.items.add(pos,item); throw e; }
        file(item).delete();
    }
}
