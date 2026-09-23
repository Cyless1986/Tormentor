package de.tormentor.app;

import java.text.Normalizer;
import java.util.Locale;

final class LoreCommands {
    static final String[] PHRASES={"starte aufnahme","starte die aufnahme","aufnahme starten","beginne aufnahme","beende aufnahme","beende die aufnahme","aufnahme beenden","stoppe aufnahme","stoppe die aufnahme","aufnahme stoppen"};
    static int action(String text){
        String value=Normalizer.normalize(text.toLowerCase(Locale.GERMAN),Normalizer.Form.NFD).replaceAll("\\p{M}","").replaceAll("[^a-z ]"," ").trim().replaceAll(" +"," ");
        value=value.replaceFirst("^(?:cortana|kortana|katana) +","");
        for(int i=0;i<PHRASES.length;i++)if(value.equals(PHRASES[i]))return i<4?1:-1;
        return 0;
    }
}
