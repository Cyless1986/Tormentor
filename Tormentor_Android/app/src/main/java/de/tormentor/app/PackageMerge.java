package de.tormentor.app;

import java.text.Normalizer;
import java.util.*;

/** Commit metadata before callers remove any superseded app-owned files. */
final class PackageMerge {
    interface Save { void run() throws Exception; }
    private static String key(String name) {
        return Normalizer.normalize(name.toLowerCase(Locale.GERMAN).replace("ß","ss"),Normalizer.Form.NFD)
            .replaceAll("\\p{M}","").replaceAll("[^a-z0-9 ]"," ").trim().replaceAll(" +"," ");
    }
    static List<Library.Item> apply(List<Library.Scene> current,List<Library.Scene> incoming,
                                   boolean replaceVideos,Save save) throws Exception {
        List<Library.Scene> before=new ArrayList<>(current);
        Map<Library.Scene,List<Library.Item>> snapshots=new HashMap<>();
        for(Library.Scene scene:before)snapshots.put(scene,new ArrayList<>(scene.items));
        List<Library.Item> removed=new ArrayList<>();
        try {
            for(Library.Scene source:incoming) {
                Library.Scene target=null;
                for(Library.Scene scene:current)if(key(scene.name).equals(key(source.name))){target=scene;break;}
                if(target==null){current.add(source);continue;}
                for(Library.Item item:source.items) {
                    if(replaceVideos && item.kind.equals("video")) {
                        Iterator<Library.Item> iterator=target.items.iterator();
                        while(iterator.hasNext()) {
                            Library.Item old=iterator.next();
                            if(old.kind.equals("video") && old.name.equals(item.name)) {
                                removed.add(old);iterator.remove();
                            }
                        }
                    }
                    target.items.add(item);
                }
            }
            save.run();
            return removed;
        } catch(Exception e) {
            current.clear();current.addAll(before);
            for(Library.Scene scene:before){scene.items.clear();scene.items.addAll(snapshots.get(scene));}
            throw e;
        }
    }
}
