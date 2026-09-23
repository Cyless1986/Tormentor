package de.tormentor.app;
import org.junit.Test;
import static org.junit.Assert.*;
public class LocalAiTest {
    @Test public void permitsPrivateLaptop() throws Exception {assertEquals("http://192.168.1.10:8765",LocalAi.address("http://192.168.1.10"));assertEquals("http://10.0.0.2:8765",LocalAi.address("http://10.0.0.2:8765/"));assertEquals("http://172.16.1.2:8765",LocalAi.address("http://172.16.1.2"));}
    @Test public void rejectsPublicAndCredentialUrls(){for(String url:new String[]{"http://example.com","http://8.8.8.8","http://user:password@192.168.1.1","http://192.168.1.1/path","http://192.168.1.999","http://172.32.0.1"}){try{LocalAi.address(url);fail(url);}catch(java.io.IOException expected){}}}
}
