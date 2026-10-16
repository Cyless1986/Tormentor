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
import org.vosk.SpeakerModel;
import org.vosk.android.StorageService;

/** A single microphone feeds both the private recording and offline voice commands. */
final class OfflineVoice {
    interface Events { void status(String text); void heard(String text); void failed(String text); java.util.List<String> phrases(); }
    private volatile Model model;
    private volatile SpeakerModel speakerModel;
    interface TrainingEvents { void update(String message, int sample, boolean finished); }
    private SpeakerProfile training;
    private TrainingEvents trainingEvents;
    private volatile boolean trainingActive;
    private volatile double[] voiceProfile;
    private volatile boolean voiceFilter;
    private long lastRejected;
    private volatile boolean wanted,closed,dictation,paused;
    private boolean loading;
    private volatile int recognitionGeneration;
    private volatile String grammar;
    private Thread worker;
    private PcmWaveFile recording;
    private final Context context;
    private final Events events;
    private final Handler main=new Handler(Looper.getMainLooper());
    OfflineVoice(Context context,Events events){
        this.context=context;this.events=events;
        try{voiceProfile=vector(new JSONArray(preferences().getString("profile","[]")));}catch(Exception ignored){}
        voiceFilter=preferences().getBoolean("enabled",false);
    }
    private android.content.SharedPreferences preferences(){return context.getSharedPreferences("speaker-profile",Context.MODE_PRIVATE);}
    synchronized boolean hasVoiceProfile(){return voiceProfile!=null;}
    boolean voiceFilterEnabled(){return voiceFilter;}
    synchronized void setVoiceFilter(boolean enabled){voiceFilter=enabled;preferences().edit().putBoolean("enabled",enabled).apply();recognitionGeneration++;}
    synchronized void deleteVoiceProfile(){voiceProfile=null;voiceFilter=false;preferences().edit().clear().apply();recognitionGeneration++;}
    synchronized void train(TrainingEvents listener){training=new SpeakerProfile();trainingEvents=listener;trainingActive=true;dictation=false;paused=false;start();}
    synchronized void cancelTraining(){trainingActive=false;training=null;trainingEvents=null;recognitionGeneration++;}
    private static double[] vector(JSONArray array){
        if(array==null||array.length()!=SpeakerProfile.DIMENSIONS)return null;
        double[] values=new double[array.length()];for(int i=0;i<values.length;i++)values[i]=array.optDouble(i,Double.NaN);
        return SpeakerProfile.unit(values);
    }
    private synchronized void trainingResult(JSONObject result)throws org.json.JSONException{
        if(!trainingActive||training==null)return;
        int frames=result.optInt("spk_frames");double[] vector=vector(result.optJSONArray("spk"));
        String message;boolean finished=false;
        if(training.count()<SpeakerProfile.TRAINING_SAMPLES){
            message=training.add(vector,frames)?"Probe übernommen. Nach einer kurzen Pause den nächsten Satz sprechen.":"Probe zu kurz oder nicht ähnlich genug. Bitte allein, deutlich und etwa 5 Sekunden sprechen.";
        }else if(SpeakerProfile.matches(training.average(),vector,frames)){
            double[] candidate=training.average();
            if(preferences().edit().putString("profile",new JSONArray(candidate).toString()).putBoolean("enabled",true).commit()){
                voiceProfile=candidate;voiceFilter=true;trainingActive=false;recognitionGeneration++;finished=true;
                message="Stimmprofil gespeichert und Stimmfilter eingeschaltet.";
            }else message="Speichern fehlgeschlagen. Bitte die Prüfprobe wiederholen.";
        }else message="Prüfprobe passt noch nicht. Bitte denselben Satz ruhig wiederholen oder neu einlernen.";
        final String notice=message;final boolean done=finished;final int count=training.count();final TrainingEvents listener=trainingEvents;
        main.post(()->{synchronized(OfflineVoice.this){if(!closed&&trainingEvents==listener&&listener!=null)listener.update(notice,count,done);}});
    }
    void start(){
        if(closed)return;
        wanted=true;
        JSONArray phrases=new JSONArray(VoicePhrases.build(events.phrases()));
        grammar=phrases.toString();recognitionGeneration++;
        if(model!=null&&speakerModel!=null){startRecorder();return;}
        if(loading)return;
        loading=true;events.status("Cortana: Offline-Sprachmodell wird geladen …");
        StorageService.unpack(context,"model-de","speech-model",loaded->{
            if(closed){loading=false;loaded.close();return;}
            new Thread(()->{
                SpeakerModel speaker=null;
                try{
                    File directory=new File(context.getFilesDir(),"speaker-model-0.4");
                    copyModel("model-spk",directory);speaker=new SpeakerModel(directory.getAbsolutePath());
                    final SpeakerModel ready=speaker;
                    main.post(()->{loading=false;if(closed){ready.close();loaded.close();return;}model=loaded;speakerModel=ready;if(wanted||isRecording())startRecorder();});
                }catch(Exception|LinkageError error){if(speaker!=null)speaker.close();loaded.close();main.post(()->{loading=false;wanted=false;if(!closed)events.failed("Stimmenmodell: "+error.getMessage());});}
            },"Tormentor-Stimmenmodell").start();
        },error->{loading=false;wanted=false;if(!closed)events.failed("Sprachmodell: "+error.getMessage());});
    }
    private void copyModel(String source,File target)throws IOException{
        String[] children=context.getAssets().list(source);
        if(children!=null&&children.length>0){if(!target.isDirectory()&&!target.mkdirs())throw new IOException("Modellordner nicht anlegbar");for(String child:children)copyModel(source+"/"+child,new File(target,child));}
        else try(InputStream in=context.getAssets().open(source);OutputStream out=new FileOutputStream(target)){byte[] buffer=new byte[8192];int n;while((n=in.read(buffer))!=-1)out.write(buffer,0,n);}
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
                    if(!wanted||paused||model==null||speakerModel==null)continue;
                    if(recognizer==null){recognizer=(dictation||trainingActive)?new Recognizer(model,16000f):new Recognizer(model,16000f,grammar);recognizer.setWords(true);recognizer.setSpeakerModel(speakerModel);activeGeneration=current;}
                    if(recognizer.acceptWaveForm(bytes,size)){
                        JSONObject result=new JSONObject(recognizer.getResult());
                        String text=result.optString("text");
                        if(current!=recognitionGeneration)continue;
                        if(trainingActive){if(!text.isEmpty())trainingResult(result);continue;}
                        // Wake-only may acknowledge as before, but never executes anything.
                        // Every subsequent command needs its own matching speaker vector.
                        // Cortana's playback is excluded by pause(); enrollment stays stricter.
                        if(voiceFilter&&!text.isEmpty()&&!WakeGate.isWakeOnly(text)&&!SpeakerProfile.matchesCommand(voiceProfile,vector(result.optJSONArray("spk")),result.optInt("spk_frames"))){
                            long now=android.os.SystemClock.elapsedRealtime();
                            if(now-lastRejected>4000){lastRejected=now;final String hint=result.optInt("spk_frames")<50?"Stimmfilter: Stimme zu kurz erfasst. Bitte den Befehl ruhig wiederholen.":"Stimmfilter: Stimme passt nicht sicher zum gespeicherten Profil. Bitte allein sprechen oder unter Meine Stimme neu einlernen.";main.post(()->{if(!closed&&wanted)events.status(hint);});}
                            continue;
                        }
                        // Reject uncertain wake words produced by the constrained grammar.
                        if(!dictation&&WakeGate.WAKE.matcher(text).find()){
                            JSONArray words=result.optJSONArray("result");
                            int wakeIndex=(text.startsWith("hey ")||text.startsWith("hallo "))?1:0;
                            if(words==null||words.length()<=wakeIndex||words.getJSONObject(wakeIndex).optDouble("conf",0)<0.85)continue;
                        }
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
                synchronized(OfflineVoice.this){worker=null;if(closed){if(model!=null){model.close();model=null;}if(speakerModel!=null){speakerModel.close();speakerModel=null;}}}
                main.post(()->{if(!closed&&(wanted||isRecording()))startRecorder();});
            }
        },"Tormentor-Mikrofon");
        worker.start();
    }
    void pause(boolean value){paused=value;recognitionGeneration++;}
    void dictation(boolean value){dictation=value;recognitionGeneration++;}
    void stop(){wanted=false;cancelTraining();recognitionGeneration++;}
    synchronized void close(){closed=true;stop();try{stopRecording();}catch(IOException ignored){}if(worker==null){if(model!=null){model.close();model=null;}if(speakerModel!=null){speakerModel.close();speakerModel=null;}}}
}
