package de.tormentor.app;

import android.annotation.SuppressLint;
import android.content.Context;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Handler;
import android.os.Looper;
import java.io.*;
import org.json.JSONArray;
import org.json.JSONObject;
import org.vosk.Model;
import org.vosk.Recognizer;
import org.vosk.android.StorageService;

/** A single microphone feeds both the private recording and offline voice commands. */
final class OfflineVoice {
    interface Events { void status(String text); void heard(String text); void failed(String text); java.util.List<String> phrases(); }
    private volatile Model model;
    private volatile boolean wanted,closed,dictation,paused;
    private boolean loading;
    private volatile int recognitionGeneration;
    private volatile String grammar;
    private Thread worker;
    private PcmWaveFile recording;
    private final Context context;
    private final Events events;
    private final Handler main=new Handler(Looper.getMainLooper());
    OfflineVoice(Context context,Events events){this.context=context;this.events=events;}
    void start(){
        if(closed)return;
        wanted=true;
        JSONArray phrases=new JSONArray();
        phrases.put("katana");phrases.put("stopp");phrases.put("stop");phrases.put("katana stopp");phrases.put("katana stop");
        for(String phrase:events.phrases()){phrases.put(phrase);phrases.put("spiele "+phrase);phrases.put("katana spiele "+phrase);phrases.put("katana "+phrase);}
        for(String phrase:LoreCommands.PHRASES){phrases.put(phrase);phrases.put("katana "+phrase);}
        phrases.put("frage");phrases.put("katana frage");phrases.put("frage tor mentor");phrases.put("katana frage tor mentor");phrases.put("[unk]");
        grammar=phrases.toString();recognitionGeneration++;
        if(model!=null){startRecorder();return;}
        if(loading)return;
        loading=true;events.status("Cortana: Offline-Sprachmodell wird geladen …");
        StorageService.unpack(context,"model-de","speech-model",loaded->{loading=false;if(closed){loaded.close();return;}model=loaded;if(wanted)startRecorder();},error->{loading=false;wanted=false;events.failed("Sprachmodell: "+error.getMessage());});
    }
    synchronized boolean isRecording(){return recording!=null;}
    synchronized void startRecording(File file)throws IOException{
        if(closed)throw new IOException("Mikrofon ist geschlossen.");
        if(recording!=null)throw new IOException("Es läuft bereits eine Aufnahme.");
        recording=new PcmWaveFile(file);startRecorder();
    }
    synchronized void stopRecording()throws IOException{
        if(recording!=null){PcmWaveFile current=recording;recording=null;current.close();}
    }
    private synchronized void saveAudio(byte[] bytes,int size)throws IOException{if(recording!=null)recording.write(bytes,size);}
    @SuppressLint("MissingPermission") // MainActivity requests RECORD_AUDIO before either entry point.
    private synchronized void startRecorder(){
        if(closed||worker!=null||(!wanted&&!isRecording()))return;
        worker=new Thread(()->{
            AudioRecord microphone=null;Recognizer recognizer=null;
            int activeGeneration=-1;
            try{
                int minimum=AudioRecord.getMinBufferSize(16000,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT);
                if(minimum<=0)throw new IOException("16-kHz-Aufnahme wird auf diesem Gerät nicht unterstützt.");
                microphone=new AudioRecord(MediaRecorder.AudioSource.MIC,16000,AudioFormat.CHANNEL_IN_MONO,AudioFormat.ENCODING_PCM_16BIT,Math.max(minimum,64000));
                if(microphone.getState()!=AudioRecord.STATE_INITIALIZED)throw new IOException("Mikrofon nicht verfügbar.");
                microphone.startRecording();
                if(microphone.getRecordingState()!=AudioRecord.RECORDSTATE_RECORDING)throw new IOException("Mikrofon konnte nicht gestartet werden.");
                byte[] bytes=new byte[3200];
                while(!closed&&(wanted||isRecording())){
                    int size=microphone.read(bytes,0,bytes.length);
                    if(size<0)throw new IOException("Mikrofon meldet Fehler "+size);
                    if(size==0)continue;
                    saveAudio(bytes,size);
                    int current=recognitionGeneration;
                    if(recognizer!=null&&(!wanted||paused||current!=activeGeneration)){recognizer.close();recognizer=null;}
                    if(!wanted||paused||model==null)continue;
                    if(recognizer==null){recognizer=dictation?new Recognizer(model,16000f):new Recognizer(model,16000f,grammar);activeGeneration=current;}
                    if(recognizer.acceptWaveForm(bytes,size)){
                        String text=new JSONObject(recognizer.getResult()).optString("text");
                        final int acceptedGeneration=activeGeneration;
                        if(!text.isEmpty())main.post(()->{if(!closed&&wanted&&!paused&&recognitionGeneration==acceptedGeneration)events.heard(text);});
                    }
                }
            }catch(Exception|LinkageError error){
                wanted=false;
                try{stopRecording();}catch(IOException ignored){}
                main.post(()->{if(!closed)events.failed("Mikrofon / Aufnahme: "+error.getMessage()+" Bereits gespeicherte Audiodaten bleiben erhalten.");});
            }finally{
                if(recognizer!=null)recognizer.close();
                if(microphone!=null){try{microphone.stop();}catch(IllegalStateException ignored){}microphone.release();}
                synchronized(OfflineVoice.this){worker=null;if(closed&&model!=null){model.close();model=null;}}
                main.post(()->{if(!closed&&(wanted||isRecording()))startRecorder();});
            }
        },"Tormentor-Mikrofon");
        worker.start();
    }
    void pause(boolean value){paused=value;recognitionGeneration++;}
    void dictation(boolean value){dictation=value;recognitionGeneration++;}
    void stop(){wanted=false;recognitionGeneration++;}
    synchronized void close(){closed=true;stop();try{stopRecording();}catch(IOException ignored){}if(worker==null&&model!=null){model.close();model=null;}}
}
