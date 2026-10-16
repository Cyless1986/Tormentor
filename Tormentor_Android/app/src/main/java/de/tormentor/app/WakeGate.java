package de.tormentor.app;

import java.util.regex.*;

/** Accept commands only after an activation word; expires using monotonic time. */
final class WakeGate {
    static final Pattern WAKE=Pattern.compile("^\\s*(?:(?:hey|hallo)\\s+)?(?:cortana|kortana|katana)\\b[,:]?",Pattern.CASE_INSENSITIVE);
    private long deadline=0;
    boolean activated=false;
    static boolean isWakeOnly(String text){
        Matcher match=WAKE.matcher(text);
        return match.find()&&text.substring(match.end()).trim().isEmpty();
    }
    String accept(String text,long now) {
        activated=false;
        Matcher match=WAKE.matcher(text);
        if(match.find()) {
            activated=true;
            String rest=text.substring(match.end()).trim();
            if(rest.isEmpty()){deadline=now+10000;return null;}
            deadline=0;return rest;
        }
        if(deadline>0 && now<=deadline && !text.trim().isEmpty()){deadline=0;return text.trim();}
        if(now>deadline)deadline=0;
        return null;
    }
    void reset(){deadline=0;activated=false;}
}
