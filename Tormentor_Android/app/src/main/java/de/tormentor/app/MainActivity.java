package de.tormentor.app;

import android.Manifest;
import android.app.*;
import android.content.*;
import android.content.pm.PackageManager;
import android.graphics.*;
import android.graphics.drawable.GradientDrawable;
import android.media.*;
import android.net.Uri;
import android.webkit.WebView;
import android.os.*;
import android.speech.*;
import android.view.*;
import android.widget.*;
import java.io.*;
import java.text.Normalizer;
import java.util.*;
import java.util.concurrent.*;
import org.json.*;

public class MainActivity extends Activity {
    private static final int GOLD=0xffe8d7b5, BG=0xff120d08, RED=0xff6e1717, PICK=11, VOICE=12, ZIP=13, LORE_AUDIO=16, LORE_PERMISSION=17;
    private File loreRecording;
    private LoreTransfer loreTransfer;
    private boolean loreTitleOpen=false, onceListening=false;
    private Library library;
    private LinearLayout sceneButtons;
    private ScenePanel scenePanel;
    private Button sceneMenuButton;
    private boolean compactLayout;
    private TextView status, title;
    private ImageView picture;
    private BackgroundVideoView video;
    private MediaPlayer music;
    private Bitmap bitmap;
    private float volume=0.5f;
    private float voiceVolume=1f;
    private MediaPlayer voicePlayer;
    private OfflineVoice offline;
    private Button wakeButton;
    private boolean wakeEnabled=false;
    private final WakeGate wakeGate=new WakeGate();
    private final Handler handler=new Handler(Looper.getMainLooper());
    private boolean loop=true, busy=false, foreground=true;
    private Library.Scene pendingScene;
    private String pendingKind;
    private final Random random=new Random();
    private final Map<String,String> last=new HashMap<>();
    private final ExecutorService io=Executors.newSingleThreadExecutor();
    private final ExecutorService network=Executors.newSingleThreadExecutor();
    private LocalAi localRequest;
    private int requestGeneration=0;
    private boolean awaitingQuestion=false,answerPending=false,questionListening=false;
    private TextView answerText;
    private File answerFile;
    private int imageGeneration=0;
    private Dialog introDialog;
    private VideoView introVideo;
    private MediaPlayer introMusic;
    private AudioManager audio;
    private final AudioManager.OnAudioFocusChangeListener focus=change -> {
        if(change==AudioManager.AUDIOFOCUS_LOSS || change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT) stopPlayback();
        else if(music!=null) { float v=change==AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK?volume*0.2f:volume; music.setVolume(v,v); }
    };
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        audio=(AudioManager)getSystemService(AUDIO_SERVICE);
        volume=getPreferences(0).getFloat("volume",0.5f);
        voiceVolume=getPreferences(0).getFloat("voiceVolume",1f);
        loop=getPreferences(0).getBoolean("loop",true);
        if(state!=null) { pendingKind=state.getString("pendingKind"); }
        try { library=new Library(this); }
        catch(Exception e) { new AlertDialog.Builder(this).setTitle("Bibliothek konnte nicht geladen werden").setMessage(e.getMessage()+"\nDie gespeicherten Medien bleiben erhalten.").setPositiveButton("Schließen",(d,w)->finish()).setCancelable(false).show(); return; }
        if(state!=null) for(Library.Scene scene:library.scenes) if(scene.id.equals(state.getString("pendingScene"))) pendingScene=scene;
        buildUi();
        offline=new OfflineVoice(this,new OfflineVoice.Events(){
            public void status(String text){report(text);}
            public void heard(String text){if(!foreground||(!wakeEnabled&&!onceListening)||busy||voicePlayer!=null||answerPending)return;if(onceListening){finishOnce();command(text);return;}if(awaitingQuestion){endQuestion();if(normalize(text).equals("abbrechen")||normalize(text).equals("stopp")){report("Frage abgebrochen.");return;}askLocal(text,false);return;}String accepted=wakeGate.accept(text,SystemClock.elapsedRealtime());if(accepted!=null)command(accepted);else if(wakeGate.activated){report("Ja, Dungeonmaster? Sage deinen Befehl.");activationVoice();}}
            public void failed(String text){wakeEnabled=false;wakeButton.setText("Cortana einschalten");report(text);}
            public java.util.List<String> phrases(){ArrayList<String> phrases=new ArrayList<>();for(Library.Scene scene:library.scenes){phrases.add(scene.name.toLowerCase(Locale.GERMAN));phrases.add(scene.voiceName.toLowerCase(Locale.GERMAN));if(scene.name.equalsIgnoreCase("Dungeon"))phrases.add("dann gehen");}return phrases;}
        });
        if(state==null)showIntro();
    }
    private int dp(int x) { return Math.round(x*getResources().getDisplayMetrics().density); }
    private TextView label(String text,int size) { TextView t=new TextView(this); t.setText(text); t.setTextColor(GOLD); t.setTextSize(size); t.setPadding(dp(12),dp(8),dp(12),dp(8)); return t; }
    private Button button(String text,Runnable action) {
        return button(text,RED,action);
    }
    private Button button(String text,int color,Runnable action) {
        Button b=new Button(this); b.setText(text); b.setTextColor(GOLD); b.setAllCaps(false); b.setTextSize(16); b.setMinHeight(dp(54));
        GradientDrawable bg=new GradientDrawable(); bg.setColor(color); bg.setCornerRadius(dp(8)); bg.setStroke(dp(1),0xff8f6037); b.setBackground(new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(0x44ffffff),bg,null));
        LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2); p.setMargins(dp(6),dp(5),dp(6),dp(5)); b.setLayoutParams(p); b.setOnClickListener(v->action.run()); return b;
    }
    private void buildUi() {
        compactLayout=ScreenLayout.compact(getResources().getConfiguration().screenWidthDp);
        LinearLayout root=new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(BG);
        title=label("TORMENTOR",compactLayout?20:25);title.setGravity(Gravity.CENTER);root.addView(title);
        TextView version=label("Version 2.3 · Smartphone & Tablet",12);version.setGravity(Gravity.CENTER);root.addView(version);
        if(compactLayout){
            LinearLayout actions=new LinearLayout(this);
            actions.addView(button("Funktionen",0xff33281e,this::phoneMenu),new LinearLayout.LayoutParams(0,-2,1));
            actions.addView(button("Szenen / Stopp",0xff33281e,()->scenePanel.setVisibility(scenePanel.getVisibility()==View.VISIBLE?View.GONE:View.VISIBLE)),new LinearLayout.LayoutParams(0,-2,1));
            root.addView(actions);
        }
        LinearLayout body=new LinearLayout(this); root.addView(body,new LinearLayout.LayoutParams(-1,0,1));
        ScrollView scroll=new ScrollView(this); if(!compactLayout)body.addView(scroll,new LinearLayout.LayoutParams(dp(180),-1));
        LinearLayout controls=new LinearLayout(this); controls.setOrientation(LinearLayout.VERTICAL); scroll.addView(controls);
        wakeButton=button("Cortana einschalten",0xff155b78,this::toggleWake);controls.addView(wakeButton);
        controls.addView(button("Sprachbefehl einmal",0xff33281e,this::onceCommands));
        controls.addView(button("Frage Tormentor",0xff633c83,this::typedQuestion));
        controls.addView(button("Hilfe",0xff33281e,this::help));
        controls.addView(button("Würfeln",0xff28613b,this::dice));
        controls.addView(button("Medien verwalten",0xff33281e,this::chooseManager));
        controls.addView(button("Tormentor Lore",0xff33281e,this::loreMenu));
        controls.addView(button("Kampagnenportal",0xff633c83,this::openPortal));
        controls.addView(button("Lokale KI einrichten",0xff33281e,this::configureLocal));
        controls.addView(button("Intro abspielen",0xff33281e,this::showIntro));
        sceneMenuButton=button("Szenen / Stopp",0xff33281e,()->{boolean visible=scenePanel.getVisibility()==View.VISIBLE;scenePanel.setVisibility(visible?View.GONE:View.VISIBLE);});controls.addView(sceneMenuButton);sceneMenuButton.setVisibility(View.GONE);
        for(int i=0;i<controls.getChildCount();i++){View control=controls.getChildAt(i);if(control instanceof Button){LinearLayout.LayoutParams cp=(LinearLayout.LayoutParams)control.getLayoutParams();cp.height=LinearLayout.LayoutParams.WRAP_CONTENT;cp.setMargins(dp(6),dp(3),dp(6),dp(3));control.setLayoutParams(cp);}}
        FrameLayout stage=new FrameLayout(this); stage.setBackgroundColor(0xff211713); body.addView(stage,new LinearLayout.LayoutParams(0,-1,1));
        ImageView homePicture=new ImageView(this);homePicture.setScaleType(ImageView.ScaleType.CENTER_CROP);
        try(InputStream source=getAssets().open("home.png")){BitmapFactory.Options options=new BitmapFactory.Options();options.inSampleSize=2;homePicture.setImageBitmap(BitmapFactory.decodeStream(source,null,options));}catch(IOException e){report("Startbild konnte nicht geladen werden.");}
        stage.addView(homePicture,new FrameLayout.LayoutParams(-1,-1));
        video=new BackgroundVideoView(this);video.setAudioFocusRequest(AudioManager.AUDIOFOCUS_NONE); FrameLayout.LayoutParams vp=new FrameLayout.LayoutParams(-1,-1,Gravity.CENTER); stage.addView(video,vp); video.setVisibility(View.GONE);
        picture=new ImageView(this); picture.setScaleType(ImageView.ScaleType.FIT_CENTER); stage.addView(picture,new FrameLayout.LayoutParams(-1,-1)); picture.setVisibility(View.GONE);
        scenePanel=new ScenePanel(this);stage.addView(scenePanel,new FrameLayout.LayoutParams(-1,-1));
        LinearLayout sceneContent=new LinearLayout(this);sceneContent.setOrientation(LinearLayout.VERTICAL);scenePanel.addView(sceneContent);
        ScrollView sceneScroll=new ScrollView(this);sceneScroll.setFillViewport(true);sceneContent.addView(sceneScroll,new LinearLayout.LayoutParams(-1,0,1));
        sceneButtons=new LinearLayout(this);sceneButtons.setGravity(Gravity.CENTER);sceneButtons.setOrientation(LinearLayout.VERTICAL);sceneScroll.addView(sceneButtons);
        Button stop=button("■  Alles stoppen",()->{stopPlayback();showHomeBackground();report("Wiedergabe gestoppt");});
        LinearLayout stopRow=new LinearLayout(this);stopRow.setGravity(Gravity.CENTER);stopRow.addView(stop,new LinearLayout.LayoutParams(-1,-2));sceneContent.addView(stopRow);
        ScrollView answers=new ScrollView(this);answers.setBackgroundColor(0xcc120d08);answerText=label("",17);answers.addView(answerText);FrameLayout.LayoutParams ap=new FrameLayout.LayoutParams(-1,dp(160),Gravity.BOTTOM);stage.addView(answers,ap);answers.setVisibility(View.GONE);answerText.setOnClickListener(v->answers.setVisibility(View.GONE));
        LinearLayout bar=new LinearLayout(this); bar.setGravity(Gravity.CENTER_VERTICAL);bar.setOrientation(compactLayout?LinearLayout.VERTICAL:LinearLayout.HORIZONTAL); root.addView(bar);
        LinearLayout musicBar=new LinearLayout(this);musicBar.setGravity(Gravity.CENTER_VERTICAL);bar.addView(musicBar,compactLayout?new LinearLayout.LayoutParams(-1,-2):new LinearLayout.LayoutParams(0,-2,1));
        musicBar.addView(label("Musik",14)); SeekBar slider=new SeekBar(this); slider.setMax(100); slider.setProgress(Math.round(volume*100)); musicBar.addView(slider,new LinearLayout.LayoutParams(0,dp(48),1));
        slider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){ public void onStartTrackingTouch(SeekBar s){} public void onStopTrackingTouch(SeekBar s){getPreferences(0).edit().putFloat("volume",volume).apply();} public void onProgressChanged(SeekBar s,int n,boolean user){volume=n/100f;if(music!=null){float gain=voicePlayer==null?volume:volume*0.25f;music.setVolume(gain,gain);}} });
        CheckBox repeat=new CheckBox(this); repeat.setText("Schleife");repeat.setTextColor(GOLD);repeat.setChecked(loop);musicBar.addView(repeat);repeat.setOnCheckedChangeListener((b,value)->{loop=value;if(music!=null)music.setLooping(loop);getPreferences(0).edit().putBoolean("loop",loop).apply();});
        LinearLayout voiceBar=new LinearLayout(this);voiceBar.setGravity(Gravity.CENTER_VERTICAL);bar.addView(voiceBar,compactLayout?new LinearLayout.LayoutParams(-1,-2):new LinearLayout.LayoutParams(0,-2,1));voiceBar.addView(label("Stimme",14));SeekBar voiceSlider=new SeekBar(this);voiceSlider.setMax(100);voiceSlider.setProgress(Math.round(voiceVolume*100));voiceBar.addView(voiceSlider,new LinearLayout.LayoutParams(0,dp(48),1));voiceSlider.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onStartTrackingTouch(SeekBar s){}public void onStopTrackingTouch(SeekBar s){getPreferences(0).edit().putFloat("voiceVolume",voiceVolume).apply();}public void onProgressChanged(SeekBar s,int n,boolean user){voiceVolume=n/100f;if(voicePlayer!=null)voicePlayer.setVolume(voiceVolume,voiceVolume);}});
        status=label("Bereit · Android 8.1 kompatibel",14);status.setMaxLines(2);status.setEllipsize(android.text.TextUtils.TruncateAt.END); root.addView(status); setContentView(root); refreshScenes();
    }
    private void phoneMenu(){
        String[] names={wakeEnabled?"Cortana ausschalten":"Cortana einschalten","Sprachbefehl einmal","Frage Tormentor","Würfeln","Medien verwalten","Tormentor Lore","Kampagnenportal","Lokale KI einrichten","Intro abspielen","Hilfe"};
        Runnable[] actions={this::toggleWake,this::onceCommands,this::typedQuestion,this::dice,this::chooseManager,this::loreMenu,this::openPortal,this::configureLocal,this::showIntro,this::help};
        new AlertDialog.Builder(this).setTitle("Tormentor · Funktionen").setItems(names,(d,n)->actions[n].run()).setNegativeButton("Schließen",null).show();
    }
    @Override public void onConfigurationChanged(android.content.res.Configuration configuration){
        super.onConfigurationChanged(configuration);
        CharSequence message=status==null?"Bereit":status.getText();
        boolean showingIntro=introDialog!=null;
        if(showingIntro)introDialog.dismiss();
        stopPlayback();buildUi();wakeButton.setText(wakeEnabled?"Cortana ausschalten":"Cortana einschalten");
        status.setText(message);if(showingIntro)showIntro();else showHomeBackground();
    }
    private void openPortal() {
        startActivity(new Intent(this, PortalActivity.class));
    }
    private void refreshScenes() {
        sceneButtons.removeAllViews();ArrayList<Library.Scene> ordered=new ArrayList<>();
        for(String name:new String[]{"Wald","Dungeon","Bosskampf","Höhle","Taverne","Rätsel"})for(Library.Scene scene:library.scenes)if(scene.name.equalsIgnoreCase(name))ordered.add(scene);
        for(Library.Scene scene:library.scenes)if(!ordered.contains(scene))ordered.add(scene);
        LinearLayout row=null;
        int columns=ScreenLayout.columns(getResources().getConfiguration().screenWidthDp,getResources().getConfiguration().fontScale);
        for(int i=0;i<ordered.size();i++){
            Library.Scene scene=ordered.get(i);
            if(i%columns==0){row=new LinearLayout(this);sceneButtons.addView(row,new LinearLayout.LayoutParams(-1,-2));}
            Button tile=button(scene.name,()->playScene(scene));tile.setTypeface(Typeface.SERIF);tile.setTextSize(compactLayout?16:20);tile.setShadowLayer(2,0,2,Color.BLACK);tile.setMinHeight(dp(64));tile.setMinimumHeight(dp(64));tile.setPadding(dp(10),dp(5),dp(10),dp(5));
            android.graphics.drawable.Drawable slab=getDrawable(de.tormentor.app.R.drawable.stone_slab);
            tile.setBackground(new android.graphics.drawable.RippleDrawable(android.content.res.ColorStateList.valueOf(0x55e8d7b5),slab,null));
            LinearLayout.LayoutParams tp=new LinearLayout.LayoutParams(0,-2,1);tp.setMargins(dp(3),dp(3),dp(3),dp(3));row.addView(tile,tp);
            if(columns==2&&i==ordered.size()-1&&i%2==0)row.addView(new View(this),new LinearLayout.LayoutParams(0,dp(64),1));
        }
        if(offline!=null&&wakeEnabled&&foreground){offline.stop();offline.start();}
    }
    private File cachedVideo(String asset,String cacheName) throws IOException {
        File target=new File(getCacheDir(),cacheName);
        if(!target.isFile()) {
            File partial=new File(getCacheDir(),cacheName+".partial");
            try(InputStream source=getAssets().open(asset);OutputStream out=new FileOutputStream(partial)) {
                byte[] buffer=new byte[65536];int n;while((n=source.read(buffer))!=-1)out.write(buffer,0,n);
            }
            if(!partial.renameTo(target))throw new IOException("Video konnte nicht vorbereitet werden");
        }
        return target;
    }
    private void showHomeBackground() {
        if(!foreground||introDialog!=null)return;
        clearBackground();scenePanel.setVisibility(View.VISIBLE);sceneMenuButton.setVisibility(View.GONE);final int generation=imageGeneration;
        io.execute(()->{
            try {
                File target=cachedVideo("home.mp4","home-v3.mp4");
                runOnUiThread(()->{
                    if(generation!=imageGeneration||!foreground||introDialog!=null||isDestroyed())return;
                    video.setOnPreparedListener(p->{video.setCropSize(p.getVideoWidth(),p.getVideoHeight());p.setVolume(0,0);p.setLooping(true);if(generation==imageGeneration&&foreground)video.start();});
                    video.setOnErrorListener((p,w,e)->{video.setVisibility(View.GONE);return true;});
                    video.setVisibility(View.VISIBLE);video.setVideoPath(target.getAbsolutePath());
                });
            }catch(IOException e){/* The bundled still image remains visible. */}
        });
    }
    private void showIntro(){
        if(busy||introDialog!=null)return;stopPlayback();if(offline!=null)offline.stop();
        Dialog dialog=new Dialog(this,android.R.style.Theme_Material_NoActionBar_Fullscreen);introDialog=dialog;
        FrameLayout layout=new FrameLayout(this);layout.setBackgroundColor(BG);layout.setClipChildren(true);
        BackgroundVideoView view=new BackgroundVideoView(this);view.setAudioFocusRequest(AudioManager.AUDIOFOCUS_NONE);introVideo=view;layout.addView(view,new FrameLayout.LayoutParams(-1,-1,Gravity.CENTER));
        TextView heading=label("TORMENTOR",26);heading.setGravity(Gravity.CENTER);heading.setShadowLayer(4,0,2,Color.BLACK);layout.addView(heading,new FrameLayout.LayoutParams(-1,-2,Gravity.TOP));
        Button skip=button("Abenteuer starten · Intro überspringen",dialog::dismiss);FrameLayout.LayoutParams skipParams=new FrameLayout.LayoutParams(-1,-2,Gravity.BOTTOM);skipParams.setMargins(dp(16),dp(12),dp(16),dp(20));layout.addView(skip,skipParams);dialog.setContentView(layout);
        dialog.setOnDismissListener(d->{view.stopPlayback();introVideo=null;if(introMusic!=null){introMusic.release();introMusic=null;}introDialog=null;showHomeBackground();if(offline!=null&&wakeEnabled&&foreground)offline.start();});
        dialog.show();
        if(dialog.getWindow()!=null)dialog.getWindow().setLayout(-1,-1);
        io.execute(()->{File target=new File(getCacheDir(),"intro-v3.mp4");Exception failure=null;try{if(!target.isFile()){File partial=new File(getCacheDir(),"intro.partial");try(InputStream source=getAssets().open("intro.mp4");OutputStream out=new FileOutputStream(partial)){byte[] b=new byte[65536];int n;while((n=source.read(b))!=-1)out.write(b,0,n);}if(!partial.renameTo(target))throw new IOException("Intro konnte nicht vorbereitet werden");}}catch(Exception e){failure=e;}final Exception problem=failure;
            runOnUiThread(()->{if(introDialog!=dialog||!foreground||isDestroyed())return;if(problem!=null){dialog.dismiss();error(problem);return;}view.setVideoPath(target.getAbsolutePath());view.setOnPreparedListener(p->{view.setCropSize(p.getVideoWidth(),p.getVideoHeight());p.setVolume(0,0);p.setLooping(true);if(foreground&&introDialog==dialog)view.start();});view.setOnErrorListener((p,w,e)->{dialog.dismiss();report("Intro-Video nicht abspielbar.");return true;});
                try(android.content.res.AssetFileDescriptor asset=getAssets().openFd("intro.mp3")){MediaPlayer player=new MediaPlayer();introMusic=player;player.setDataSource(asset.getFileDescriptor(),asset.getStartOffset(),asset.getLength());player.setVolume(volume,volume);player.setLooping(true);player.setOnPreparedListener(p->{if(introMusic==p&&foreground)p.start();});player.setOnErrorListener((p,w,e)->{if(introMusic==p){p.release();introMusic=null;}return true;});player.prepareAsync();}catch(Exception e){report("Intro-Sound nicht verfügbar.");}
            });
        });
    }
    private void report(String text) { if(status!=null)status.setText(text); }
    private void error(Exception e) { report("Fehler: "+e.getMessage()); new AlertDialog.Builder(this).setTitle("Tormentor").setMessage(e.getMessage()).setPositiveButton("OK",null).show(); }
    private Library.Item choose(Library.Scene scene,boolean sound) {
        ArrayList<Library.Item> choices=new ArrayList<>();
        for(Library.Item item:scene.items) if(item.kind.equals("audio")==sound && library.file(item).isFile()) choices.add(item);
        String key=scene.id+sound;
        if(choices.size()>1) choices.removeIf(item->item.id.equals(last.get(key)));
        if(choices.isEmpty())return null;
        Library.Item item=choices.get(random.nextInt(choices.size())); last.put(key,item.id); return item;
    }
    private void playScene(Library.Scene scene) {
        if(busy){report("Bitte den Import abwarten.");return;}
        stopPlayback();scenePanel.setVisibility(View.GONE);sceneMenuButton.setVisibility(View.VISIBLE); title.setText("TORMENTOR  ·  "+scene.name);
        Library.Item sound=choose(scene,true), background=choose(scene,false);
        if(sound!=null)playSound(sound);
        if(background!=null)showBackground(background);
        if(sound==null && background==null)report(scene.name+": noch keine Medien. Unter „Medien verwalten“ hinzufügen.");
        else report(scene.name+" · "+(sound!=null?sound.name:"ohne Sound"));
    }
    private void playSound(Library.Item item) {
        releaseMusic();
        if(audio.requestAudioFocus(focus,AudioManager.STREAM_MUSIC,AudioManager.AUDIOFOCUS_GAIN)!=AudioManager.AUDIOFOCUS_REQUEST_GRANTED) { report("Audio wird gerade von einer anderen App verwendet."); return; }
        try {
            MediaPlayer player=new MediaPlayer(); music=player;
            player.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build());
            player.setDataSource(library.file(item).getAbsolutePath()); player.setVolume(volume,volume);player.setLooping(loop);
            player.setOnPreparedListener(p->{if(music==p && foreground)p.start();});
            player.setOnErrorListener((p,what,extra)->{report("Sound kann nicht abgespielt werden: "+item.name);if(music==p)releaseMusic();return true;}); player.prepareAsync();
        } catch(Exception e){releaseMusic();error(e);}
    }
    private void showBackground(Library.Item item) {
        clearBackground();scenePanel.setVisibility(View.GONE);sceneMenuButton.setVisibility(View.VISIBLE);
        if(item.kind.equals("video")) {
            video.setVisibility(View.VISIBLE);
            video.setOnPreparedListener(p->{p.setVolume(0,0);p.setLooping(true);if(foreground)video.start();});
            video.setOnErrorListener((p,w,e)->{video.setVisibility(View.GONE);report("Video nicht abspielbar: "+item.name+" ("+w+"/"+e+"). Tablet-Videopaket importieren; eigene Videos: H.264 Baseline, maximal 1280 × 720.");return true;});
            video.setVideoPath(library.file(item).getAbsolutePath());
        } else {
            final int generation=imageGeneration;
            io.execute(()->{
                Bitmap result=null; String failure=null;
                try { BitmapFactory.Options options=new BitmapFactory.Options();options.inJustDecodeBounds=true;BitmapFactory.decodeFile(library.file(item).getAbsolutePath(),options);options.inSampleSize=1;while(options.outWidth/options.inSampleSize>1920 || options.outHeight/options.inSampleSize>1920)options.inSampleSize*=2;options.inJustDecodeBounds=false;result=BitmapFactory.decodeFile(library.file(item).getAbsolutePath(),options);if(result==null)failure="Bild nicht lesbar: "+item.name; }
                catch(Exception | OutOfMemoryError e){failure="Bild konnte nicht geladen werden: "+item.name;}
                final Bitmap loaded=result; final String message=failure;
                runOnUiThread(()->{if(generation!=imageGeneration || isDestroyed()){if(loaded!=null)loaded.recycle();return;}if(message!=null){report(message);return;}bitmap=loaded;picture.setImageBitmap(bitmap);picture.setVisibility(View.VISIBLE);});
            });
        }
    }
    private void releaseMusic(){if(music!=null){music.release();music=null;}}
    private void clearBackground(){imageGeneration++;if(video!=null){video.stopPlayback();video.setCropSize(0,0);video.setVisibility(View.GONE);}if(picture!=null){picture.setImageDrawable(null);picture.setVisibility(View.GONE);}if(bitmap!=null){bitmap.recycle();bitmap=null;}}
    private void stopPlayback(){cancelQuestion();releaseMusic();clearBackground();finishVoice();if(audio!=null)audio.abandonAudioFocus(focus);}
    private void configureLocal(){
        LinearLayout form=new LinearLayout(this);form.setOrientation(LinearLayout.VERTICAL);form.setPadding(dp(16),0,dp(16),0);
        EditText host=new EditText(this);host.setSingleLine(true);host.setHint("http://192.168.1.10:8765");host.setText(getPreferences(0).getString("aiHost",""));form.addView(label("Laptop-Adresse",14));form.addView(host);
        EditText token=new EditText(this);token.setSingleLine(true);token.setHint("Verbindungscode");token.setInputType(android.text.InputType.TYPE_CLASS_TEXT|android.text.InputType.TYPE_TEXT_VARIATION_PASSWORD);token.setText(getPreferences(0).getString("aiToken",""));form.addView(label("Verbindungscode vom Laptop",14));form.addView(token);
        ScrollView connectionScroll=new ScrollView(this);connectionScroll.addView(form);
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("Lokale KI · ohne API-Gebühren").setMessage("Auf dem Laptop KI-starten.cmd öffnen. Beide Geräte ins gleiche private WLAN. Verbindung aus Tablet-Verbindung.txt eintragen oder die JSON-Datei importieren.").setView(connectionScroll).setNegativeButton("Schließen",null).setNeutralButton("Datei importieren",(d,w)->{Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);try{startActivityForResult(i,15);}catch(ActivityNotFoundException e){error(e);}}).setPositiveButton("Speichern & testen",null).create();
        dialog.setOnShowListener(d->dialog.getButton(-1).setOnClickListener(v->{try{saveConnection(host.getText().toString(),token.getText().toString());dialog.dismiss();askLocal("",true);}catch(Exception e){host.setError(e.getMessage());}}));dialog.show();
    }
    private void saveConnection(String host,String token)throws Exception{String validated=LocalAi.address(host);if(!token.trim().matches("[a-fA-F0-9]{32}"))throw new IOException("Verbindungscode muss 32 Zeichen lang sein.");getPreferences(0).edit().putString("aiHost",validated).putString("aiToken",token.trim()).apply();}
    private void typedQuestion(){EditText input=new EditText(this);input.setHint("Deine Frage an Tormentor");input.setMinLines(3);AlertDialog dialog=new AlertDialog.Builder(this).setTitle("Frage Tormentor").setView(input).setNegativeButton("Abbrechen",null).setPositiveButton("Fragen",null).create();dialog.setOnShowListener(d->dialog.getButton(-1).setOnClickListener(v->{String q=input.getText().toString().trim();if(q.isEmpty()||q.length()>4000){input.setError("Bitte 1 bis 4000 Zeichen eingeben");return;}dialog.dismiss();askLocal(q,false);}));dialog.show();}
    private final Runnable questionTimeout=()->{if(awaitingQuestion){endQuestion();report("Keine Frage erkannt. Sage erneut „Cortana, frage Tormentor“.");}};
    private void beginQuestion(){if(getPreferences(0).getString("aiHost","").isEmpty()){report("Bitte zuerst „Lokale KI einrichten“ öffnen.");return;}awaitingQuestion=true;questionListening=false;handler.removeCallbacks(questionTimeout);offline.pause(true);offline.dictation(true);report("Cortanas Antwort abwarten – danach öffnet sich die Frageaufnahme.");activationVoice();}
    private void endQuestion(){awaitingQuestion=false;questionListening=false;handler.removeCallbacks(questionTimeout);if(offline!=null)offline.dictation(false);}
    private void cancelQuestion(){requestGeneration++;if(localRequest!=null){localRequest.cancel();localRequest=null;}answerPending=false;if(awaitingQuestion)endQuestion();}
    private void askLocal(String question,boolean test){
        if(busy)return;String host=getPreferences(0).getString("aiHost","");String token=getPreferences(0).getString("aiToken","");if(host.isEmpty()){configureLocal();return;}
        cancelQuestion();finishVoice();answerPending=true;if(offline!=null)offline.pause(true);report(test?"Laptop-Verbindung und männliche Stimme werden getestet …":"Tormentor denkt auf deinem Laptop nach …");
        final int generation=requestGeneration;LocalAi request=new LocalAi();localRequest=request;
        network.execute(()->{JSONObject result=null;Exception failure=null;File voiceFile=null;try{result=request.ask(host,token,question,test);String encoded=result.optString("audio");if(!encoded.isEmpty()){byte[] bytes=android.util.Base64.decode(encoded,android.util.Base64.DEFAULT);voiceFile=File.createTempFile("tormentor-answer-",".wav",getCacheDir());try(OutputStream out=new FileOutputStream(voiceFile)){out.write(bytes);}}}catch(Exception e){failure=e;}final JSONObject response=result;final Exception problem=failure;final File file=voiceFile;
            runOnUiThread(()->{if(generation!=requestGeneration||!foreground||isDestroyed()){if(file!=null)file.delete();return;}answerPending=false;localRequest=null;if(problem!=null){finishVoice();report("Lokale KI: "+problem.getMessage());return;}answerText.setText(response.optString("text")+"\n\n(Zum Ausblenden antippen)");((View)answerText.getParent()).setVisibility(View.VISIBLE);if(file!=null)playAnswer(file);else{finishVoice();report(response.optString("warning","Antwort empfangen, aber keine Sprachausgabe verfügbar."));}});
        });
    }
    private void playAnswer(File file){finishVoice();answerFile=file;if(offline!=null)offline.pause(true);if(music!=null)music.setVolume(volume*0.25f,volume*0.25f);try{MediaPlayer player=new MediaPlayer();voicePlayer=player;player.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ASSISTANCE_ACCESSIBILITY).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build());player.setDataSource(file.getAbsolutePath());player.setVolume(voiceVolume,voiceVolume);player.setOnPreparedListener(p->{if(voicePlayer==p&&foreground)p.start();});player.setOnCompletionListener(p->{finishVoice();report("Antwort beendet. Neue Frage: „Cortana, frage Tormentor“.");});player.setOnErrorListener((p,w,e)->{finishVoice();report("Antworttext empfangen, Sprachausgabe nicht abspielbar.");return true;});player.prepareAsync();report("Tormentor antwortet …");}catch(Exception e){finishVoice();report("Sprachausgabe: "+e.getMessage());}}
    private void toggleWake(){if(wakeEnabled){if(awaitingQuestion)endQuestion();wakeEnabled=false;offline.stop();wakeGate.reset();wakeButton.setText("Cortana einschalten");report("Cortana ist ausgeschaltet.");return;}if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},14);return;}wakeEnabled=true;wakeButton.setText("Cortana ausschalten");offline.pause(false);offline.start();}
    private void activationVoice(){
        finishVoice();if(offline!=null)offline.pause(true);if(music!=null)music.setVolume(volume*0.25f,volume*0.25f);
        try(android.content.res.AssetFileDescriptor asset=getAssets().openFd("aktivierung.mp3")){
            MediaPlayer player=new MediaPlayer();voicePlayer=player;
            player.setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ASSISTANCE_ACCESSIBILITY).setContentType(AudioAttributes.CONTENT_TYPE_SPEECH).build());
            player.setDataSource(asset.getFileDescriptor(),asset.getStartOffset(),asset.getLength());player.setVolume(voiceVolume,voiceVolume);
            player.setOnPreparedListener(p->{if(voicePlayer==p&&foreground)p.start();});player.setOnCompletionListener(p->{wakeGate.accept("cortana",SystemClock.elapsedRealtime());finishVoice();});player.setOnErrorListener((p,w,e)->{finishVoice();return true;});player.prepareAsync();
        }catch(Exception e){finishVoice();}
    }
    private final Runnable resumeListening=()->{if(offline!=null&&foreground&&wakeEnabled&&voicePlayer==null&&!answerPending){offline.pause(false);if(awaitingQuestion&&!questionListening){questionListening=true;handler.postDelayed(questionTimeout,60000);report("Jetzt deine Frage sprechen · 60 Sekunden · danach kurz schweigen.");}}};
    private void finishVoice(){handler.removeCallbacks(resumeListening);if(voicePlayer!=null){voicePlayer.release();voicePlayer=null;}if(answerFile!=null){answerFile.delete();answerFile=null;}if(music!=null)music.setVolume(volume,volume);handler.postDelayed(resumeListening,400);}
    private void chooseManager() {
        if(busy){report("Import läuft …");return;}
        ArrayList<String> names=new ArrayList<>(); for(Library.Scene s:library.scenes)names.add(s.name+"  ("+s.items.size()+")");names.add("+ Neue Kategorie");names.add("Laptop-Medienpaket importieren (.zip)");
        new AlertDialog.Builder(this).setTitle("Sounds & Hintergründe verwalten").setItems(names.toArray(new String[0]),(d,n)->{if(n<library.scenes.size())manage(library.scenes.get(n));else if(n==library.scenes.size())editScene(null);else pickZip();}).setNegativeButton("Schließen",null).show();
    }
    private void editScene(Library.Scene existing) {
        EditText input=new EditText(this);input.setSingleLine(true);input.setText(existing==null?"":existing.name);
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle(existing==null?"Neue Kategorie":"Kategorie umbenennen").setView(input).setPositiveButton("Speichern",null).setNegativeButton("Abbrechen",null).create();
        dialog.setOnShowListener(d->dialog.getButton(-1).setOnClickListener(v->{String name=input.getText().toString().trim();if(name.isEmpty() || name.length()>60){input.setError("Bitte 1 bis 60 Zeichen eingeben");return;}for(Library.Scene s:library.scenes)if(s!=existing && normalize(s.name).equals(normalize(name))){input.setError("Kategorie bereits vorhanden");return;}Library.Scene s=existing==null?new Library.Scene(UUID.randomUUID().toString(),name):existing;String before=s.name;s.name=name;if(existing==null)library.scenes.add(s);try{library.save();dialog.dismiss();refreshScenes();manage(s);}catch(Exception e){if(existing==null)library.scenes.remove(s);else s.name=before;error(e);}}));dialog.show();
    }
    private void manage(Library.Scene scene) {
        LinearLayout panel=new LinearLayout(this);panel.setOrientation(LinearLayout.VERTICAL);panel.setPadding(dp(10),dp(4),dp(10),dp(8));
        ScrollView scroll=new ScrollView(this);scroll.addView(panel);
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle(scene.name+" · Medien").setView(scroll).setNegativeButton("Zurück",(d,w)->chooseManager()).create();
        panel.addView(button("+ Sounds hinzufügen",()->{dialog.dismiss();pick(scene,"audio");}));
        panel.addView(button("+ Bilder / MP4 hinzufügen",()->{dialog.dismiss();pick(scene,"background");}));
        panel.addView(button("Kategorie umbenennen",()->{dialog.dismiss();editScene(scene);}));
        panel.addView(button("Sprachname: "+scene.voiceName,()->{dialog.dismiss();editVoiceName(scene);}));
        panel.addView(button("Kategorie löschen",()->new AlertDialog.Builder(this).setTitle("Kategorie löschen?").setMessage("„"+scene.name+"“ und ihre App-Kopien entfernen? Die Originaldateien bleiben erhalten.").setPositiveButton("Löschen",(d,w)->{stopPlayback();int pos=library.scenes.indexOf(scene);library.scenes.remove(scene);try{library.save();for(Library.Item item:scene.items)library.file(item).delete();dialog.dismiss();refreshScenes();}catch(Exception e){library.scenes.add(pos,scene);error(e);}}).setNegativeButton("Abbrechen",null).show()));
        panel.addView(label("Tippe eine Datei für Vorschau oder Löschen.\n"+scene.items.size()+" gespeicherte Dateien",14));
        for(Library.Item item:scene.items)panel.addView(button((item.kind.equals("audio")?"♫ ":item.kind.equals("video")?"▶ ":"▧ ")+item.name,()->new AlertDialog.Builder(this).setTitle(item.name).setItems(new String[]{"Vorschau abspielen","Aus App löschen"},(d,n)->{if(n==0){if(item.kind.equals("audio"))playSound(item);else showBackground(item);report("Vorschau: "+item.name);}else new AlertDialog.Builder(this).setTitle("Datei aus App löschen?").setMessage(item.name+"\nDie Originaldatei bleibt erhalten.").setPositiveButton("Löschen",(x,w)->{stopPlayback();try{library.remove(scene,item);dialog.dismiss();manage(scene);}catch(Exception e){error(e);}}).setNegativeButton("Abbrechen",null).show();}).show()));
        dialog.show();
    }
    private void editVoiceName(Library.Scene scene){EditText input=new EditText(this);input.setSingleLine(true);input.setText(scene.voiceName);AlertDialog dialog=new AlertDialog.Builder(this).setTitle("Sprachname für "+scene.name).setMessage("Verwende ein gut erkennbares deutsches Wort, zum Beispiel „Verlies“ für Dungeon. Danach: „Cortana, spiele Verlies“.").setView(input).setNegativeButton("Abbrechen",(d,w)->manage(scene)).setPositiveButton("Speichern",null).create();dialog.setOnShowListener(d->dialog.getButton(-1).setOnClickListener(v->{String value=input.getText().toString().trim();if(value.isEmpty()||value.length()>60){input.setError("Bitte 1 bis 60 Zeichen");return;}for(Library.Scene other:library.scenes)if(other!=scene&&(normalize(other.voiceName).equals(normalize(value))||normalize(other.name).equals(normalize(value)))){input.setError("Sprachname bereits vergeben");return;}String before=scene.voiceName;scene.voiceName=value;try{library.save();dialog.dismiss();refreshScenes();manage(scene);}catch(Exception e){scene.voiceName=before;error(e);}}));dialog.show();}
    private void pick(Library.Scene scene,String kind) {
        pendingScene=scene;pendingKind=kind;
        Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);intent.addCategory(Intent.CATEGORY_OPENABLE);intent.setType(kind.equals("audio")?"audio/*":"*/*");
        if(!kind.equals("audio"))intent.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"image/*","video/mp4"});
        intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE,true);
        try{startActivityForResult(intent,PICK);}catch(ActivityNotFoundException e){error(new IOException("Keine Dateiauswahl installiert."));}
    }
    private void pickZip(){Intent i=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("*/*").addCategory(Intent.CATEGORY_OPENABLE);try{startActivityForResult(i,ZIP);}catch(ActivityNotFoundException e){error(e);}}
    private File loreDir(){File folder=new File(getFilesDir(),"lore");if(!folder.exists())folder.mkdirs();return folder;}
    private boolean loreIsRecording(){return offline!=null&&offline.isRecording();}
    private void onceCommands(){
        new AlertDialog.Builder(this).setTitle("Einmal-Befehle").setItems(new String[]{"Aufnahme starten","Aufnahme beenden","Sprachbefehl sprechen"},(dialog,choice)->{if(choice==0)startLoreRecording();else if(choice==1)stopLoreRecording();else listen();}).show();
    }
    private void loreMenu(){
        String[] actions={loreIsRecording()?"Aufnahme beenden":"Sitzung aufnehmen","Audiodatei importieren","Aufnahmen anzeigen / zum Laptop übertragen"};
        new AlertDialog.Builder(this).setTitle("Tormentor Lore · nur DM").setItems(actions,(d,choice)->{
            if(choice==0){if(loreIsRecording())stopLoreRecording();else startLoreRecording();}
            else if(choice==1){Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT).setType("audio/*").addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(intent,LORE_AUDIO);}
            else showLoreRecordings();
        }).show();
    }
    private void startLoreRecording(){
        if(loreIsRecording()){report("Es läuft bereits eine Lore-Aufnahme.");return;}
        if(loreTitleOpen)return;
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},LORE_PERMISSION);return;}
        EditText input=new EditText(this);input.setSingleLine(true);input.setHint("Zum Beispiel Session 4");input.setText("Session "+new java.text.SimpleDateFormat("dd.MM.yyyy HH:mm",Locale.GERMAN).format(new Date()));input.selectAll();
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("Neue Session aufnehmen").setMessage("Sitzungstitel eingeben. Während der Aufnahme die App geöffnet lassen. Beim Verlassen wird die Aufnahme gespeichert.").setView(input).setNegativeButton("Abbrechen",null).setPositiveButton("Aufnahme starten",null).create();
        loreTitleOpen=true;dialog.setOnDismissListener(d->loreTitleOpen=false);
        dialog.setOnShowListener(d->dialog.getButton(-1).setOnClickListener(v->{String sessionTitle=input.getText().toString().trim();if(sessionTitle.isEmpty()||sessionTitle.length()>200){input.setError("Bitte 1 bis 200 Zeichen eingeben.");return;}beginLoreRecording(sessionTitle);dialog.dismiss();}));dialog.show();
    }
    private void beginLoreRecording(String sessionTitle){
        try{
            loreRecording=new File(loreDir(),"sitzung-"+UUID.randomUUID()+".wav");
            saveLoreTitle(loreRecording,sessionTitle);
            offline.startRecording(loreRecording);
            report("● Aufnahme läuft: "+sessionTitle+" · Beenden über Einmal-Befehle oder Cortana.");
        }catch(Exception e){error(e);}
    }
    private void stopLoreRecording(){
        if(!loreIsRecording()){report("Es läuft gerade keine Lore-Aufnahme.");return;}
        try{offline.stopRecording();report("Lore-Aufnahme gespeichert: "+loreTitle(loreRecording));}
        catch(IOException e){error(e);}
    }
    private void saveLoreTitle(File audioFile,String sessionTitle)throws Exception{
        File target=new File(audioFile.getPath()+".json"), temporary=new File(audioFile.getPath()+".json.tmp");
        try(OutputStream output=new FileOutputStream(temporary)){output.write(new JSONObject().put("title",sessionTitle).toString().getBytes(java.nio.charset.StandardCharsets.UTF_8));}
        if(!temporary.renameTo(target))throw new IOException("Sitzungstitel konnte nicht gespeichert werden.");
    }
    private String loreTitle(File audioFile){
        if(audioFile==null)return "Sitzung";
        try(InputStream input=new FileInputStream(audioFile.getPath()+".json");ByteArrayOutputStream output=new ByteArrayOutputStream()){
            byte[] bytes=new byte[1024];int count;while((count=input.read(bytes))!=-1){if(output.size()+count>16000)break;output.write(bytes,0,count);}
            return new JSONObject(output.toString("UTF-8")).optString("title",audioFile.getName());
        }catch(Exception ignored){return audioFile.getName();}
    }
    private void showLoreRecordings(){
        File[] files=loreDir().listFiles(file->file.isFile()&&file.getName().matches("(?i).+\\.(wav|m4a|mp3|ogg|flac|aac|mp4|audio)")&&!(loreIsRecording()&&file.equals(loreRecording)));
        if(files==null||files.length==0){report("Noch keine beendeten Lore-Aufnahmen vorhanden.");return;}
        Arrays.sort(files,(left,right)->Long.compare(right.lastModified(),left.lastModified()));
        String[] names=new String[files.length];for(int i=0;i<files.length;i++)names[i]=loreTitle(files[i])+" · "+String.format(Locale.GERMAN,"%.1f MB",files[i].length()/1048576d);
        new AlertDialog.Builder(this).setTitle("Private Lore-Aufnahmen").setItems(names,(dialog,choice)->editLoreRecording(files[choice])).show();
    }
    private void editLoreRecording(File file){
        EditText input=new EditText(this);input.setSingleLine(true);input.setText(loreTitle(file));
        AlertDialog dialog=new AlertDialog.Builder(this).setTitle("Sitzungstitel").setMessage("Aufnahmen bleiben privat. Auf dem Laptop kannst du sie auswerten und die Ergebnisse prüfen.").setView(input).setNegativeButton("Schließen",null).setNeutralButton("Titel speichern",null).setPositiveButton("Zum Laptop übertragen",null).create();
        dialog.setOnShowListener(d->{View.OnClickListener action=v->{String sessionTitle=input.getText().toString().trim();if(sessionTitle.isEmpty()||sessionTitle.length()>200){input.setError("Bitte 1 bis 200 Zeichen.");return;}try{saveLoreTitle(file,sessionTitle);if(v==dialog.getButton(-1))sendLoreRecording(file,sessionTitle);dialog.dismiss();}catch(Exception e){error(e);}};dialog.getButton(-1).setOnClickListener(action);dialog.getButton(-3).setOnClickListener(action);});dialog.show();
    }
    private void sendLoreRecording(File file,String sessionTitle){
        if(loreTransfer!=null){report("Es läuft bereits eine Übertragung.");return;}
        String host=getPreferences(0).getString("aiHost",""), token=getPreferences(0).getString("aiToken","");
        if(host.isEmpty()){configureLocal();return;}
        LoreTransfer transfer=new LoreTransfer();loreTransfer=transfer;
        report("Lore-Aufnahme wird zum Laptop übertragen: "+sessionTitle);
        network.execute(()->{try{JSONObject result=transfer.send(host,token,file,sessionTitle);runOnUiThread(()->{loreTransfer=null;if(!isDestroyed())report(result.optString("message"));});}catch(Exception e){runOnUiThread(()->{loreTransfer=null;if(!isDestroyed())error(e);});}});
    }
    @Override protected void onActivityResult(int request,int result,Intent data) {
        super.onActivityResult(request,result,data);if(result!=RESULT_OK || data==null)return;
        if(request==15&&data.getData()!=null){try(InputStream in=getContentResolver().openInputStream(data.getData());ByteArrayOutputStream bytes=new ByteArrayOutputStream()){if(in==null)throw new IOException("Datei nicht lesbar");byte[] b=new byte[1024];int n;while((n=in.read(b))!=-1){if(bytes.size()+n>10000)throw new IOException("Verbindungsdatei zu groß");bytes.write(b,0,n);}JSONObject config=new JSONObject(bytes.toString("UTF-8"));saveConnection(config.getString("host"),config.getString("token"));askLocal("",true);}catch(Exception e){error(e);}return;}
        if(request==VOICE){ArrayList<String> words=data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);if(words!=null&&!words.isEmpty())command(words.get(0));return;}
        if(request==ZIP && data.getData()!=null){importZip(data.getData());return;}
        if(request==LORE_AUDIO && data.getData()!=null){
            final Uri uri=data.getData();io.execute(()->{File output=new File(loreDir(),"import-"+UUID.randomUUID()+".audio");try(InputStream input=getContentResolver().openInputStream(uri)){
                if(input==null)throw new IOException("Audiodatei nicht lesbar");
                try(FileOutputStream stream=new FileOutputStream(output)){byte[] bytes=new byte[8192];int count;long size=0;while((count=input.read(bytes))!=-1){size+=count;if(size>1024L*1024*1024)throw new IOException("Maximal 1 GB pro Aufnahme.");stream.write(bytes,0,count);}if(size==0)throw new IOException("Die Audiodatei ist leer.");}
                saveLoreTitle(output,"Importierte Sitzung");
                runOnUiThread(()->{if(!isDestroyed())editLoreRecording(output);});
            }catch(Exception e){output.delete();runOnUiThread(()->{if(!isDestroyed())error(e);});}});return;
        }
        if(request!=PICK || pendingScene==null)return;
        ArrayList<Uri> uris=new ArrayList<>();if(data.getClipData()!=null)for(int j=0;j<data.getClipData().getItemCount();j++)uris.add(data.getClipData().getItemAt(j).getUri());else if(data.getData()!=null)uris.add(data.getData());
        final Library.Scene scene=pendingScene;final String requested=pendingKind;pendingScene=null;pendingKind=null;
        busy=true;report("Dateien werden in den App-Speicher kopiert …");
        io.execute(()->{int count=0;ArrayList<String> errors=new ArrayList<>();for(Uri uri:uris){try{String name=library.name(uri);String kind=Library.kind(name,getContentResolver().getType(uri));if(kind.equals("audio")!=requested.equals("audio"))throw new IOException("Unpassende Datei: "+name);try(InputStream source=getContentResolver().openInputStream(uri)){if(source==null)throw new IOException("Datei nicht lesbar");library.add(scene,library.copy(source,name,kind));}count++;}catch(Exception e){errors.add(e.getMessage());}}final int imported=count;runOnUiThread(()->{busy=false;if(isDestroyed())return;report(imported+" Datei(en) in „"+scene.name+"“ hinzugefügt.");if(!errors.isEmpty())error(new IOException(String.join("\n",errors)));else manage(scene);});});
    }
    private void importZip(Uri uri) {
        stopPlayback();busy=true;report("Medienpaket wird importiert …");
        io.execute(()->{ArrayList<Library.Scene> staged=new ArrayList<>();ArrayList<Library.Item> copied=new ArrayList<>();Exception failure=null;boolean committed=false;
            try(java.util.zip.ZipInputStream zip=new java.util.zip.ZipInputStream(getContentResolver().openInputStream(uri))) {
                java.util.zip.ZipEntry first=zip.getNextEntry();if(first==null || !first.getName().equals("manifest.json"))throw new IOException("Kein Tormentor-Medienpaket: manifest.json muss der erste Eintrag sein.");
                ByteArrayOutputStream manifest=new ByteArrayOutputStream();byte[] buffer=new byte[8192];int n;while((n=zip.read(buffer))!=-1){if(manifest.size()+n>4*1024*1024)throw new IOException("Manifest zu groß");manifest.write(buffer,0,n);}
                JSONObject packageInfo=new JSONObject(manifest.toString("UTF-8"));boolean replaceVideos=packageInfo.optBoolean("replaceVideosByName",false);JSONArray scenes=packageInfo.getJSONArray("scenes");Map<String,Library.Scene> targets=new HashMap<>();Map<String,JSONObject> entries=new HashMap<>();
                for(int i=0;i<scenes.length();i++){JSONObject s=scenes.getJSONObject(i);String name=s.getString("name").trim();if(name.isEmpty()||name.length()>60)throw new IOException("Ungültiger Kategoriename");Library.Scene scene=new Library.Scene(UUID.randomUUID().toString(),name);staged.add(scene);JSONArray items=s.getJSONArray("items");for(int j=0;j<items.length();j++){JSONObject item=items.getJSONObject(j);String path=item.getString("path");if(entries.containsKey(path))throw new IOException("Doppelter Paketeintrag");entries.put(path,item);targets.put(path,scene);}}
                java.util.zip.ZipEntry entry;while((entry=zip.getNextEntry())!=null){JSONObject item=entries.remove(entry.getName());if(item==null){throw new IOException("Unbekannter Paketeintrag: "+entry.getName());}String kind=Library.kind(item.getString("name"),null);Library.Item copiedItem=library.copy(zip,item.getString("name"),kind);copied.add(copiedItem);targets.get(entry.getName()).items.add(copiedItem);}
                if(!entries.isEmpty())throw new IOException("Medienpaket unvollständig");
                // Commit the entire package once; roll back index changes on any save failure.
                synchronized(library){List<Library.Item> replaced=PackageMerge.apply(library.scenes,staged,replaceVideos,library::save);committed=true;for(Library.Item old:replaced)library.file(old).delete();}
                committed=true;
            }catch(Exception e){failure=e;if(!committed)for(Library.Item item:copied)library.file(item).delete();}
            final Exception problem=failure;runOnUiThread(()->{busy=false;if(isDestroyed())return;refreshScenes();if(problem!=null)error(problem);else report(copied.size()+" Medien importiert. Deine Szenen sind bereit.");});
        });
    }
    private final Runnable onceTimeout=()->{if(onceListening){finishOnce();report("Kein Befehl erkannt. Bitte erneut antippen.");}};
    private void finishOnce(){onceListening=false;handler.removeCallbacks(onceTimeout);if(offline!=null&&!wakeEnabled)offline.stop();}
    private void listen(){
        if(busy){report("Bitte den Import abwarten.");return;}
        if(checkSelfPermission(Manifest.permission.RECORD_AUDIO)!=PackageManager.PERMISSION_GRANTED){requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO},VOICE);return;}
        cancelQuestion();finishVoice();onceListening=true;offline.dictation(false);offline.pause(false);offline.start();
        handler.removeCallbacks(onceTimeout);handler.postDelayed(onceTimeout,20000);
        report("Jetzt einen Befehl sprechen, etwa „Starte Aufnahme“ oder „Beende Aufnahme“.");
    }
    @Override public void onRequestPermissionsResult(int r,String[] p,int[] g){super.onRequestPermissionsResult(r,p,g);if(r==LORE_PERMISSION){if(g.length>0&&g[0]==PackageManager.PERMISSION_GRANTED)startLoreRecording();else report("Mikrofon nicht freigegeben.");return;}if(r==VOICE||r==14){if(g.length>0&&g[0]==PackageManager.PERMISSION_GRANTED){if(r==14)toggleWake();else listen();}else report("Mikrofon nicht freigegeben. Die Szenentasten funktionieren weiterhin.");}}
    static String normalize(String text){return Normalizer.normalize(text.toLowerCase(Locale.GERMAN).replace("ß","ss"),Normalizer.Form.NFD).replaceAll("\\p{M}","").replaceAll("[^a-z0-9 ]"," ").trim().replaceAll(" +"," ");}
    private void command(String text){int recordingAction=LoreCommands.action(text);if(recordingAction==1){startLoreRecording();return;}if(recordingAction==-1){stopLoreRecording();return;}String cmd=" "+normalize(text)+" ";if(cmd.contains(" frage ")){beginQuestion();return;}if(cmd.contains(" stopp ")||cmd.contains(" stop ")){stopPlayback();showHomeBackground();report("Cortana: Wiedergabe gestoppt");return;}Library.Scene best=null;for(Library.Scene scene:library.scenes)if((cmd.contains(" "+normalize(scene.name)+" ")||cmd.contains(" "+normalize(scene.voiceName)+" ")||(scene.name.equalsIgnoreCase("Dungeon")&&cmd.contains(" dann gehen ")))&&(best==null||scene.name.length()>best.name.length()))best=scene;if(best!=null){playScene(best);return;}if(cmd.contains(" wurfel ")||cmd.contains(" wurfle ")){dice();return;}report("Erkannt: "+text+" · Sage „Spiele“ und den Kategorienamen oder „Stopp“.");}
    private void dice(){String[] names={"W4","W6","W8","W10","W12","W20","W100"};int[] sides={4,6,8,10,12,20,100};new AlertDialog.Builder(this).setTitle("Würfel wählen").setItems(names,(d,n)->report(names[n]+" → "+(random.nextInt(sides[n])+1))).show();}
    private void help(){new AlertDialog.Builder(this).setTitle("Tormentor auf deinem Tablet").setMessage("Medien verwalten → Kategorie → Sounds oder Bilder / MP4 hinzufügen. Mehrfachauswahl ist möglich. Die App speichert eigene Kopien. Zum Entfernen eine Datei antippen.\n\nEine Szene wählt zufällig einen Sound und einen Hintergrund ihrer Kategorie. Videos laufen stumm in Schleife. Empfohlen: MP3, JPG/PNG und MP4 mit H.264 Baseline bis 1280 × 720 Pixel und 30 Bildern/s.\n\n„Cortana einschalten“ antippen und das Mikrofon freigeben. Danach hört die App offline zu: „Cortana, spiele Taverne“ oder „Cortana, Stopp“. Alternativ erst „Cortana“ sagen, die Antwort abwarten und innerhalb von zehn Sekunden den Befehl sprechen. Die App muss geöffnet bleiben. Die zusätzliche Taste „Sprachbefehl einmal“ verwendet den Android-Sprachdienst und benötigt möglicherweise Internet.\n\nBeim Verlassen der App stoppt die Wiedergabe. Beim Löschen der App werden ihre Medienkopien gelöscht.\n\nDie vorhandene Cortana-Aktivierungsantwort und das Intro sind übernommen. Musik und Cortana-Stimme haben getrennte Lautstärken. Lokale KI-Antworten mit der männlichen Thorsten-Stimme sind integriert. Auf dem Laptop KI-starten.cmd öffnen; beide Geräte müssen im gleichen WLAN sein. Unter „Lokale KI einrichten“ die Tablet-Verbindung.json importieren. Mit „Frage Tormentor“ eine Frage eintippen oder „Cortana, frage Tormentor“ sagen, Cortanas Antwort abwarten. Sobald unten „Jetzt deine Frage sprechen“ steht, hast du 60 Sekunden für die Frage. Danach kurz schweigen, damit das Satzende erkannt wird. Für jede weitere Frage erneut „Cortana, frage Tormentor“ sagen. Die Frage wird offline erkannt, die Antwort auf dem Laptop berechnet und vorgelesen. Musik wird während der Antwort leiser. Es werden keine OpenAI- oder ElevenLabs-Dienste verwendet.").setPositiveButton("OK",null).show();}
    @Override protected void onSaveInstanceState(Bundle out){super.onSaveInstanceState(out);if(pendingScene!=null)out.putString("pendingScene",pendingScene.id);out.putString("pendingKind",pendingKind);}
    @Override protected void onStart(){super.onStart();foreground=true;showHomeBackground();if(offline!=null&&wakeEnabled)offline.start();}
    @Override protected void onStop(){foreground=false;finishOnce();if(loreIsRecording())stopLoreRecording();if(introDialog!=null)introDialog.dismiss();if(offline!=null)offline.stop();wakeGate.reset();stopPlayback();super.onStop();}
    @Override protected void onDestroy(){if(loreTransfer!=null)loreTransfer.cancel();stopPlayback();handler.removeCallbacksAndMessages(null);if(offline!=null)offline.close();io.shutdown();network.shutdown();super.onDestroy();}
}













