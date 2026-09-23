package de.tormentor.app;

import java.util.regex.*;

/** Accept commands only after an activation word; expires using monotonic time. */
final class WakeGate {
    private final Pattern wake=Pattern.compile("\\b(?:cortana|cotana|contana|kortana|katana)\\b",Pattern.CASE_INSENSITIVE);
    private long deadline=0;
    boolean activated=false;
    String accept(String text,long now) {
        activated=false;
        Matcher match=wake.matcher(text);
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
