package de.tormentor.app;

import org.junit.Test;
import java.io.IOException;
import java.util.*;
import static org.junit.Assert.*;

public class PackageMergeTest {
    private Library.Item item(String id,String name,String kind){return new Library.Item(id,name,kind);}
    private Library.Scene scene(String name,Library.Item... items){Library.Scene s=new Library.Scene(name,name);Collections.addAll(s.items,items);return s;}
    @Test public void repairReplacesDuplicatesButPreservesSoundPicturesAndOtherVideos() throws Exception {
        Library.Item sound=item("a","01.mp4","audio"), image=item("b","map.png","image"), other=item("c","02.mp4","video");
        Library.Scene existing=scene("Höhle",item("v1","01.mp4","video"),sound,image,other,item("v2","01.mp4","video"));
        Library.Item replacement=item("v3","01.mp4","video");
        List<Library.Scene> current=new ArrayList<>(Arrays.asList(existing));
        List<Library.Item> removed=PackageMerge.apply(current,Arrays.asList(scene("Höhle",replacement)),true,()->{});
        assertEquals(2,removed.size());assertEquals(Arrays.asList(sound,image,other,replacement),existing.items);
        assertEquals("Höhle",existing.voiceName);
        PackageMerge.apply(current,Arrays.asList(scene("Höhle",item("v4","01.mp4","video"))),true,()->{});
        assertEquals(4,existing.items.size());
    }
    @Test public void failedSaveRestoresOriginalOrderAndCategories() throws Exception {
        Library.Item original=item("v1","01.mp4","video");Library.Scene existing=scene("Wald",original);
        List<Library.Scene> current=new ArrayList<>(Arrays.asList(existing));
        try {
            PackageMerge.apply(current,Arrays.asList(scene("Wald",item("v2","01.mp4","video")),scene("Neu")),true,()->{throw new IOException("disk full");});
            fail("Expected save failure");
        }catch(IOException expected){}
        assertEquals(Arrays.asList(existing),current);assertEquals(Arrays.asList(original),existing.items);
    }
    @Test public void normalImportStillAppends() throws Exception {
        Library.Scene existing=scene("Wald",item("v1","01.mp4","video"));
        List<Library.Item> removed=PackageMerge.apply(new ArrayList<>(Arrays.asList(existing)),Arrays.asList(scene("Wald",item("v2","01.mp4","video"))),false,()->{});
        assertTrue(removed.isEmpty());assertEquals(2,existing.items.size());
    }
}
