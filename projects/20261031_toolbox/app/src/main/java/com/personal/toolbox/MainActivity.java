package com.personal.toolbox;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import android.view.MotionEvent;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.text.Editable;
import android.text.TextWatcher;
import android.view.Gravity;
import android.view.inputmethod.InputMethodManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.CheckBox;
import android.widget.SeekBar;
import android.widget.Spinner;
import android.widget.ArrayAdapter;
import android.view.WindowManager;
import java.util.Locale;
import java.util.Random;

public class MainActivity extends Activity {
    private Game view;
    private int tab = 1;
    private boolean inGame;
    private String screen = "home";
    private String displayText = "Hello!";
    private int displaySize = 64, textColor = 0, backgroundColor = 1;
    private boolean italic;
    private final int[] colors = {Color.WHITE, Color.BLACK, Color.RED, Color.YELLOW, Color.GREEN, Color.BLUE};
    private final String[] colorNames = {"White", "Black", "Red", "Yellow", "Green", "Blue"};
    private final String[] tools = {"Display", "Ruler"};
    private final String[] games = {"2048", "Minesweeper", "Flappy Bird"};
    @Override public void onCreate(Bundle state) { super.onCreate(state); view = new Game(); showHome(); }
    @Override public void onBackPressed() {
        if (screen.equals("display")) { getWindow().getDecorView().setSystemUiVisibility(0); getWindow().clearFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); showDisplaySettings(); }
        else if (!screen.equals("home")) { inGame = false; view.running = false; showHome(); }
        else super.onBackPressed();
    }
    @Override protected void onPause() { super.onPause(); if (view != null && view.mode == 3 && view.running) { view.elapsed += android.os.SystemClock.uptimeMillis() - view.lastTime; view.running = false; view.message = "Paused - tap to continue"; } }

    private void showHome() {
        screen = "home";
        LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); root.setBackgroundColor(0xfff8f6f0);
        LinearLayout body = new LinearLayout(this); body.setOrientation(LinearLayout.VERTICAL); body.setPadding(24, 16, 24, 0);
        if (tab == 1) body.setGravity(Gravity.CENTER_VERTICAL);
        EditText search = new EditText(this); search.setSingleLine(true); search.setHint(tab == 0 ? "Search tools" : tab == 2 ? "Search games" : "Search tools and games");
        body.addView(search, new LinearLayout.LayoutParams(-1, -2));
        ScrollView scroll = new ScrollView(this); LinearLayout results = new LinearLayout(this); results.setOrientation(LinearLayout.VERTICAL); scroll.addView(results);
        body.addView(scroll, new LinearLayout.LayoutParams(-1, tab == 1 ? -2 : 0, tab == 1 ? 0 : 1));
        root.addView(body, new LinearLayout.LayoutParams(-1, 0, 1));
        LinearLayout navigation = new LinearLayout(this); String[] labels = {"Tools", "Search", "Games"};
        for (int i = 0; i < labels.length; i++) { final int selected = i; Button button = new Button(this); button.setAllCaps(false); button.setText(labels[i]); button.setTextColor(i == tab ? 0xff236781 : Color.DKGRAY); button.setOnClickListener(v -> { tab = selected; showHome(); }); navigation.addView(button, new LinearLayout.LayoutParams(0, -2, 1)); }
        root.addView(navigation); setContentView(root);
        Runnable update = () -> {
            results.removeAllViews(); String query = search.getText().toString().trim().toLowerCase(Locale.ROOT); int matches = 0;
            if (tab != 2 && (tab == 0 || !query.isEmpty())) for (int i = 0; i < tools.length; i++) if (tools[i].toLowerCase(Locale.ROOT).contains(query)) {
                final int tool = i; Button button = new Button(this); button.setAllCaps(false); button.setText(tools[i]); button.setOnClickListener(v -> { ((InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(search.getWindowToken(), 0); if (tool == 0) showDisplaySettings(); else showRuler(); }); results.addView(button); matches++;
            }
            if (tab != 0 && (tab == 2 || !query.isEmpty())) for (int i = 0; i < games.length; i++) if (games[i].toLowerCase(Locale.ROOT).contains(query)) {
                final int game = i + 1; Button button = new Button(this); button.setAllCaps(false); button.setText(games[i]); button.setOnClickListener(v -> { ((InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(search.getWindowToken(), 0); inGame = true; screen = "game"; view.start(game); setContentView(view); }); results.addView(button); matches++;
            }
            if (matches == 0 && !query.isEmpty()) { TextView empty = new TextView(this); empty.setText("No matching tools"); empty.setPadding(8, 20, 8, 20); results.addView(empty); }
        };
        search.addTextChangedListener(new TextWatcher() { public void beforeTextChanged(CharSequence s, int start, int count, int after) {} public void onTextChanged(CharSequence s, int start, int before, int count) { update.run(); } public void afterTextChanged(Editable s) {} });
        update.run(); root.setFocusableInTouchMode(true); root.requestFocus();
    }

    private TextView label(String value) { TextView t = new TextView(this); t.setText(value); t.setTextSize(16); return t; }
    private Spinner colorPicker(int selection) { Spinner spinner = new Spinner(this); spinner.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_dropdown_item, colorNames)); spinner.setSelection(selection); return spinner; }
    private void showDisplaySettings() {
        screen = "settings";
        ScrollView scroll = new ScrollView(this); LinearLayout form = new LinearLayout(this); form.setOrientation(LinearLayout.VERTICAL); form.setPadding(32, 24, 32, 24); scroll.addView(form);
        TextView title = label("Display"); title.setTextSize(24); form.addView(title);
        form.addView(label("Text")); EditText input = new EditText(this); input.setText(displayText); form.addView(input);
        form.addView(label("Text size (sp)")); EditText size = new EditText(this); size.setInputType(android.text.InputType.TYPE_CLASS_NUMBER); size.setText(String.valueOf(displaySize)); form.addView(size);
        form.addView(label("Text color")); Spinner foreground = colorPicker(textColor); form.addView(foreground);
        form.addView(label("Background color")); Spinner background = colorPicker(backgroundColor); form.addView(background);
        CheckBox slant = new CheckBox(this); slant.setText("Italic"); slant.setChecked(italic); form.addView(slant);
        Button show = new Button(this); show.setText("Show"); form.addView(show); setContentView(scroll);
        show.setOnClickListener(v -> {
            String text = input.getText().toString(); if (text.trim().isEmpty()) { input.setError("Enter text"); return; }
            int parsed; try { parsed = Integer.parseInt(size.getText().toString()); } catch (NumberFormatException e) { size.setError("Enter a size from 12 to 200"); return; }
            if (parsed < 12 || parsed > 200) { size.setError("Enter a size from 12 to 200"); return; }
            displayText = text.replace('\n', ' '); displaySize = parsed; textColor = foreground.getSelectedItemPosition(); backgroundColor = background.getSelectedItemPosition(); italic = slant.isChecked();
            ((InputMethodManager)getSystemService(INPUT_METHOD_SERVICE)).hideSoftInputFromWindow(input.getWindowToken(), 0);
            screen = "display"; getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON); getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY); setContentView(new DisplayView());
        });
    }
    private class DisplayView extends View {
        Paint paint = new Paint(3); float position; long last;
        DisplayView() { super(MainActivity.this); }
        @Override protected void onDraw(Canvas canvas) { super.onDraw(canvas); canvas.drawColor(colors[backgroundColor]); paint.setColor(colors[textColor]); paint.setTextSize(displaySize * getResources().getDisplayMetrics().scaledDensity); paint.setTypeface(italic ? android.graphics.Typeface.create(android.graphics.Typeface.DEFAULT, android.graphics.Typeface.ITALIC) : android.graphics.Typeface.DEFAULT); long now = android.os.SystemClock.uptimeMillis(); if (last == 0) position = getWidth(); else position -= (now-last) * getResources().getDisplayMetrics().density * .08f; last = now; float width = paint.measureText(displayText); if (position + width < 0) position = getWidth(); canvas.drawText(displayText, position, getHeight()/2f - (paint.ascent()+paint.descent())/2, paint); postInvalidateOnAnimation(); }
    }
    private void showRuler() {
        screen = "ruler"; LinearLayout root = new LinearLayout(this); root.setOrientation(LinearLayout.VERTICAL); RulerView ruler = new RulerView(); root.addView(ruler, new LinearLayout.LayoutParams(-1, 0, 1));
        TextView info = label("Calibration: compare the marks with a physical ruler"); info.setGravity(Gravity.CENTER); root.addView(info);
        SeekBar scale = new SeekBar(this); scale.setMax(100); scale.setProgress(getPreferences(MODE_PRIVATE).getInt("rulerScale", 50)); root.addView(scale);
        scale.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() { public void onProgressChanged(SeekBar bar, int value, boolean user) { ruler.scale = .5f + value / 100f; info.setText("Calibration: " + (50 + value) + "%"); if (user) getPreferences(MODE_PRIVATE).edit().putInt("rulerScale", value).apply(); ruler.invalidate(); } public void onStartTrackingTouch(SeekBar bar) {} public void onStopTrackingTouch(SeekBar bar) {} });
        ruler.scale = .5f + scale.getProgress()/100f; info.setText("Calibration: " + (50 + scale.getProgress()) + "%"); setContentView(root);
    }
    private class RulerView extends View {
        Paint paint = new Paint(3); float scale = 1;
        RulerView() { super(MainActivity.this); }
        @Override protected void onDraw(Canvas c) { super.onDraw(c); c.drawColor(Color.WHITE); float dpi = getResources().getDisplayMetrics().ydpi * scale; float density = getResources().getDisplayMetrics().density; float origin = 20*density; paint.setColor(Color.BLACK); paint.setStrokeWidth(density); paint.setTextSize(12*density);
            for(int mm=0; origin+mm*dpi/25.4f<getHeight(); mm++) { float y=origin+mm*dpi/25.4f; float length=(mm%10==0?24:mm%5==0?16:9)*density; c.drawLine(0,y,length,y,paint); if(mm%10==0)c.drawText(String.valueOf(mm/10),length+3*density,y+4*density,paint); }
            for(int tick=0; origin+tick*dpi/16f<getHeight(); tick++) { float y=origin+tick*dpi/16f; float length=(tick%16==0?24:tick%8==0?18:tick%4==0?14:9)*density; c.drawLine(getWidth()-length,y,getWidth(),y,paint); if(tick%16==0){String s=String.valueOf(tick/16);c.drawText(s,getWidth()-length-4*density-paint.measureText(s),y+4*density,paint);} }
        }
    }

    private class Game extends View {
        final Paint p = new Paint(3); final Random random = new Random();
        int mode = 0, score, result; String message = ""; boolean running, started, won;
        int[][] cells = new int[9][9]; boolean[][] mines = new boolean[9][9], flags = new boolean[9][9], revealed = new boolean[9][9];
        float downX, downY, birdY, velocity, pipeX, gapY; long downTime, lastTime, elapsed; boolean scored;
        float w, h, board, left, top, unit;
        Game() { super(MainActivity.this); }
        void text(Canvas c, String s, float x, float y, float size, int color) { p.setColor(color); p.setTextSize(size); p.setTextAlign(Paint.Align.CENTER); p.setTypeface(android.graphics.Typeface.DEFAULT_BOLD); c.drawText(s, x, y, p); }
        void rect(Canvas c, float x, float y, float width, float height, int color) { p.setColor(color); c.drawRoundRect(x,y,x+width,y+height,12,12,p); }
        @Override protected void onDraw(Canvas c) {
            super.onDraw(c); w=getWidth(); h=getHeight(); c.drawColor(Color.rgb(248,246,240));
            float title=Math.min(w*.08f, 38*getResources().getDisplayMetrics().density);
            if (mode==0) {
                text(c,"Toolbox",w/2,h*.18f,title,Color.rgb(49,55,68));
                String[] names={"2048","Minesweeper","Flappy Bird"};
                for(int i=0;i<3;i++) { float y=h*.29f+i*h*.16f; rect(c,w*.1f,y,w*.8f,h*.11f,Color.rgb(67,112,132)); text(c,names[i],w/2,y+h*.07f,title*.8f,Color.WHITE); } return;
            }
            text(c, mode==1?"2048":mode==2?"Minesweeper":"Flappy Bird",w/2,h*.07f,title,Color.rgb(49,55,68));
            text(c,mode==2?"Flags: "+countFlags()+" / 10":mode==3?"Score: "+score+"    Time: "+(elapsed/1000)+"s":"Score: "+score,w/2,h*.125f,title*.55f,Color.DKGRAY);
            rect(c,w*.32f,h*.16f,w*.36f,h*.07f,Color.rgb(67,112,132)); text(c,"New Game",w/2,h*.207f,title*.52f,Color.WHITE);
            if(mode==3) { drawBird(c,title); return; }
            int n=mode==1?4:9; board=Math.min(w*.94f,h*.65f); left=(w-board)/2; top=h*.28f; unit=board/n;
            for(int r=0;r<n;r++) for(int col=0;col<n;col++) {
                float x=left+col*unit,y=top+r*unit; int color; String s="";
                if(mode==1) { int v=cells[r][col]; color=v==0?0xffd9d2c6:v<8?0xffeee4da:v<128?0xfff2b179:0xffedc850; if(v!=0)s=""+v; }
                else { color=revealed[r][col]?0xffe5e1d8:0xff829aa1; if(revealed[r][col]) { if(mines[r][col]) s="*"; else if(cells[r][col]>0)s=""+cells[r][col]; } }
                rect(c,x+2,y+2,unit-4,unit-4,color); if(!s.isEmpty()) text(c,s,x+unit/2,y+unit*.65f,unit*(mode==1?.32f:.42f),Color.rgb(54,55,54));
                if(mode==2 && flags[r][col] && !revealed[r][col]) { p.setColor(Color.DKGRAY); p.setStrokeWidth(Math.max(2,unit*.045f)); c.drawLine(x+unit*.38f,y+unit*.2f,x+unit*.38f,y+unit*.78f,p); Path flag = new Path(); flag.moveTo(x+unit*.4f,y+unit*.22f); flag.lineTo(x+unit*.75f,y+unit*.34f); flag.lineTo(x+unit*.4f,y+unit*.48f); flag.close(); p.setColor(Color.RED); c.drawPath(flag,p); }
            }
            text(c,message,w/2,Math.min(h*.96f,top+board+title),title*.5f,Color.DKGRAY);
        }
        void start(int game) { mode=game; score=0; result=0; message=""; running=false; started=false; won=false; cells=new int[9][9]; mines=new boolean[9][9]; flags=new boolean[9][9]; revealed=new boolean[9][9];
            if(game==1) { addTile(); addTile(); message="Swipe to move"; }
            if(game==2) message="Tap to reveal; hold to flag";
            if(game==3) { birdY=.5f; velocity=0; pipeX=1.1f; gapY=.5f; elapsed=0; scored=false; message="Tap to start"; }
            invalidate();
        }
        void addTile() { int empty=0; for(int r=0;r<4;r++)for(int c=0;c<4;c++)if(cells[r][c]==0)empty++; if(empty==0)return; int pick=random.nextInt(empty); for(int r=0;r<4;r++)for(int c=0;c<4;c++)if(cells[r][c]==0 && pick--==0){cells[r][c]=random.nextInt(10)==0?4:2; return;} }
        void move(int dr,int dc) {
            boolean changed=false;
            for(int line=0;line<4;line++) { int[] old=new int[4], out=new int[4]; int size=0;
                for(int i=0;i<4;i++){int r=dr==0?line:(dr<0?i:3-i), c=dc==0?line:(dc<0?i:3-i); old[i]=cells[r][c]; if(old[i]!=0)out[size++]=old[i];}
                for(int i=0;i<size-1;i++)if(out[i]==out[i+1]){out[i]*=2; score+=out[i]; if(out[i]>=2048&&!won){won=true;message="2048 reached! Keep playing";} for(int j=i+1;j<size-1;j++)out[j]=out[j+1]; out[--size]=0;}
                for(int i=0;i<4;i++){int r=dr==0?line:(dr<0?i:3-i), c=dc==0?line:(dc<0?i:3-i); if(old[i]!=out[i])changed=true; cells[r][c]=out[i];}
            }
            if(changed)addTile(); boolean can=false; for(int r=0;r<4;r++)for(int c=0;c<4;c++)if(cells[r][c]==0||(r<3&&cells[r][c]==cells[r+1][c])||(c<3&&cells[r][c]==cells[r][c+1]))can=true;
            if(!can){result=1;message="No moves left - game over";} invalidate();
        }
        int countFlags(){int n=0;for(int r=0;r<9;r++)for(int c=0;c<9;c++)if(flags[r][c])n++;return n;}
        void placeMines(int firstR,int firstC){ int n=0; while(n<10){int r=random.nextInt(9),c=random.nextInt(9);if(!mines[r][c]&&(r!=firstR||c!=firstC)){mines[r][c]=true;n++;}} for(int r=0;r<9;r++)for(int c=0;c<9;c++)for(int a=Math.max(0,r-1);a<=Math.min(8,r+1);a++)for(int b=Math.max(0,c-1);b<=Math.min(8,c+1);b++)if(mines[a][b])cells[r][c]++; }
        void reveal(int r,int c){if(r<0||r>=9||c<0||c>=9||revealed[r][c]||flags[r][c])return;revealed[r][c]=true;if(cells[r][c]==0&&!mines[r][c])for(int a=r-1;a<=r+1;a++)for(int b=c-1;b<=c+1;b++)reveal(a,b);}
        void mineTap(int r,int c,boolean hold){ if(result!=0||revealed[r][c])return; if(hold){flags[r][c]=!flags[r][c];} else if(!flags[r][c]){if(!started){placeMines(r,c);started=true;} if(mines[r][c]){result=1;message="Mine hit - game over";for(int a=0;a<9;a++)for(int b=0;b<9;b++)if(mines[a][b])revealed[a][b]=true;}else{reveal(r,c);int n=0;for(int a=0;a<9;a++)for(int b=0;b<9;b++)if(revealed[a][b])n++;if(n==71){result=1;message="You win!";}}} invalidate(); }
        void drawBird(Canvas c,float title){
            float y0=h*.27f, height=h*.65f; rect(c,0,y0,w,height,0xffb7e3ed);
            if(running){long now=android.os.SystemClock.uptimeMillis();long delta=now-lastTime;elapsed+=delta;float dt=Math.min(delta/1000f,.04f);lastTime=now;velocity+=1.5f*dt;birdY+=velocity*dt;pipeX-=(.35f+elapsed/1000f*.006f)*dt;if(!scored&&pipeX+.14f<.24f){score++;scored=true;}if(pipeX<-.18f){pipeX=1.05f;gapY=.3f+random.nextFloat()*.4f;scored=false;}if(birdY<.03f||birdY>.97f||(pipeX<.29f&&pipeX+.14f>.19f&&(birdY-.035f<gapY-.15f||birdY+.035f>gapY+.15f))){running=false;result=1;message="Game over - New Game to retry";}else postInvalidateOnAnimation();}
            rect(c,pipeX*w,y0,w*.14f,height*(gapY-.15f),0xff4f9e66);rect(c,pipeX*w,y0+height*(gapY+.15f),w*.14f,height*(.85f-gapY),0xff4f9e66);p.setColor(0xffffc843);c.drawCircle(w*.24f,y0+birdY*height,w*.05f,p);text(c,message,w/2,h*.97f,title*.48f,Color.DKGRAY);
        }
        @Override public boolean onTouchEvent(MotionEvent e){float x=e.getX(), y=e.getY();if(e.getAction()==MotionEvent.ACTION_DOWN){downX=x;downY=y;downTime=android.os.SystemClock.uptimeMillis();return true;} if(e.getAction()!=MotionEvent.ACTION_UP)return true;
            if(mode==0){for(int i=0;i<3;i++)if(y>=h*.29f+i*h*.16f&&y<=h*.40f+i*h*.16f){start(i+1);break;}return true;}
            if(y>=h*.16f&&y<=h*.23f&&x>=w*.32f&&x<=w*.68f){start(mode);return true;}
            if(mode==1&&result==0){float dx=x-downX,dy=y-downY;if(Math.max(Math.abs(dx),Math.abs(dy))>w*.08f){if(Math.abs(dx)>Math.abs(dy))move(0,dx<0?-1:1);else move(dy<0?-1:1,0);}}
            else if(mode==2&&x>=left&&x<left+board&&y>=top&&y<top+board&&Math.abs(x-downX)<unit&&Math.abs(y-downY)<unit)mineTap((int)((y-top)/unit),(int)((x-left)/unit),android.os.SystemClock.uptimeMillis()-downTime>=500);
            else if(mode==3&&result==0){if(!running)lastTime=android.os.SystemClock.uptimeMillis();running=true;message="";velocity=-.53f;invalidate();}return true;
        }
    }
}
