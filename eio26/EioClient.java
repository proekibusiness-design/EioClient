package com.eio.client;

import com.mojang.brigadier.arguments.StringArgumentType;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.command.v2.*;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.fabricmc.fabric.api.client.screen.v1.ScreenEvents;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.client.*;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.gui.screens.TitleScreen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import org.lwjgl.glfw.GLFW;
import java.awt.Color;
import java.io.*;
import java.nio.file.*;
import java.util.*;

public final class EioClient implements ClientModInitializer {
  public static final String VERSION="0.7.0";
  private static final int GUI_KEY=GLFW.GLFW_KEY_RIGHT_SHIFT;
  private static final List<Mod> MODS=new ArrayList<>();
  private static final Map<Integer,Boolean> KEY_PREV=new HashMap<>();
  private static boolean guiPrev;
  private static int autoClickTicks;
  private static final Path CONFIG=FabricLoader.getInstance().getConfigDir().resolve("eioclient.properties");

  static {
    add("Kill Aura","Combat","Attacks the entity you are aiming at automatically.",-1);
    add("Auto Clicker","Combat","Repeats the attack key while enabled.",-1);
    add("Sprint","Movement","Automatically sprints while moving forward.",GLFW.GLFW_KEY_R);
    add("AutoWalk","Movement","Keeps moving forward until disabled.",GLFW.GLFW_KEY_G);
    add("Fly","Movement","Enables creative-style client flight.",GLFW.GLFW_KEY_F);
    add("Coordinates","Render","Shows your XYZ position.",-1);
    add("FPS","Render","Shows current FPS.",-1);
    add("Active Modules","Render","Lists enabled modules on the HUD.",-1);
    add("Fullbright","Render","Raises client gamma while enabled.",-1);
    add("Session Info","Misc","Shows the Eio version in the HUD.",-1);
    add("Notifications","Misc","Shows module toggle feedback in chat.",-1);
  }
  private static void add(String n,String c,String d,int key){MODS.add(new Mod(n,c,d,key));}

  @Override public void onInitializeClient(){
    load();
    ClientTickEvents.END_CLIENT_TICK.register(EioClient::tick);
    HudElementRegistry.addLast(Identifier.fromNamespaceAndPath("eioclient","hud"),EioClient::hud);
    ScreenEvents.AFTER_INIT.register((client,screen,w,h)->{
      if(screen instanceof TitleScreen) ScreenEvents.afterExtract(screen).register((s,g,mx,my,delta)->drawBrand(g,s.width));
    });
    ClientCommandRegistrationCallback.EVENT.register((d,a)->d.register(ClientCommands.literal("eio")
      .executes(c->{openGui();return 1;})
      .then(ClientCommands.literal("gui").executes(c->{openGui();return 1;}))
      .then(ClientCommands.literal("list").executes(c->{c.getSource().sendFeedback(Component.literal(summary()));return 1;}))
      .then(ClientCommands.literal("toggle").then(ClientCommands.argument("module",StringArgumentType.greedyString()).executes(c->{Mod m=find(StringArgumentType.getString(c,"module"));if(m==null){c.getSource().sendFeedback(Component.literal("Unknown module"));return 0;}toggle(m);return 1;})))));
  }

  private static long window(){return Minecraft.getInstance().getWindow().getHandle();}
  private static boolean key(int k){return k>=0&&GLFW.glfwGetKey(window(),k)==GLFW.GLFW_PRESS;}
  private static void openGui(){Minecraft.getInstance().setScreenAndShow(new ClickGui());}
  private static void tick(Minecraft mc){
    boolean gd=key(GUI_KEY);
    if(gd&&!guiPrev) openGui();
    guiPrev=gd;
    for(Mod m:MODS) if(m.key>=0){boolean d=key(m.key),p=KEY_PREV.getOrDefault(m.key,false);if(d&&!p)toggle(m);KEY_PREV.put(m.key,d);}
    if(mc.player==null)return;
    Mod walk=find("AutoWalk"), sprint=find("Sprint"), fly=find("Fly"), click=find("Auto Clicker"), aura=find("Kill Aura");
    if(walk.enabled)mc.options.keyUp.setDown(true);
    if(sprint.enabled&&mc.options.keyUp.isDown()&&mc.player.getFoodData().getFoodLevel()>6&&!mc.player.horizontalCollision)mc.player.setSprinting(true);
    if(fly.enabled){var a=mc.player.getAbilities();a.allowFlying=true;a.flying=true;}
    if(click.enabled){autoClickTicks++;mc.options.keyAttack.setDown((autoClickTicks%2)==0);} else {autoClickTicks=0;}
    if(aura.enabled)mc.options.keyAttack.setDown(true);
  }

  private static void hud(GuiGraphicsExtractor g,DeltaTracker dt){
    Minecraft mc=Minecraft.getInstance();if(mc.player==null)return;int y=5;
    g.text(mc.font,"Eio",5,y,0xFF8CCDF2,true);y+=11;
    if(find("Session Info").enabled){g.text(mc.font,"v"+VERSION+" / MC 26.3",5,y,0xFF8795A3,false);y+=10;}
    if(find("Coordinates").enabled){g.text(mc.font,String.format(Locale.ROOT,"XYZ %.1f  %.1f  %.1f",mc.player.getX(),mc.player.getY(),mc.player.getZ()),5,y,0xFFD9E0E6,true);y+=11;}
    if(find("FPS").enabled){g.text(mc.font,"FPS "+mc.getFps(),5,y,0xFFD9E0E6,true);y+=11;}
    if(find("Active Modules").enabled)for(Mod m:MODS)if(m.enabled&&!Set.of("Active Modules","Coordinates","FPS","Session Info").contains(m.name)){g.text(mc.font,m.name,5,y,0xFF91BDD8,true);y+=10;}
  }
  private static void drawBrand(GuiGraphicsExtractor g,int width){Minecraft mc=Minecraft.getInstance();String t="Made by Eio";int x=width-mc.font.width(t)-7,y=7;long now=System.currentTimeMillis();for(int i=0;i<t.length();i++){String c=t.substring(i,i+1);float h=((now%8000L)/8000f+i*.035f)%1f;int rgb=Color.HSBtoRGB(h,.32f,1f);g.text(mc.font,c,x,y,0xFF000000|rgb,false);x+=mc.font.width(c);}}

  private static Mod find(String n){for(Mod m:MODS)if(m.name.equalsIgnoreCase(n))return m;return null;}
  private static void toggle(Mod m){
    m.enabled=!m.enabled;Minecraft mc=Minecraft.getInstance();
    if(m.name.equals("AutoWalk")&&!m.enabled)mc.options.keyUp.setDown(false);
    if((m.name.equals("Auto Clicker")||m.name.equals("Kill Aura"))&&!m.enabled)mc.options.keyAttack.setDown(false);
    if(m.name.equals("Fly")&&!m.enabled&&mc.player!=null){var a=mc.player.getAbilities();boolean legit=mc.player.isCreative()||mc.player.isSpectator();a.allowFlying=legit;if(!legit)a.flying=false;}
    save();
  }
  private static String summary(){StringJoiner j=new StringJoiner(" | ");for(Mod m:MODS)j.add(m.name+":"+(m.enabled?"ON":"OFF"));return j.toString();}
  private static void load(){Properties p=new Properties();try(InputStream in=Files.newInputStream(CONFIG)){p.load(in);}catch(Exception ignored){}for(Mod m:MODS){m.enabled=Boolean.parseBoolean(p.getProperty("enabled."+m.name,"false"));try{m.key=Integer.parseInt(p.getProperty("key."+m.name,Integer.toString(m.key)));}catch(Exception ignored){}}}
  private static void save(){Properties p=new Properties();for(Mod m:MODS){p.setProperty("enabled."+m.name,Boolean.toString(m.enabled));p.setProperty("key."+m.name,Integer.toString(m.key));}try{Files.createDirectories(CONFIG.getParent());try(OutputStream out=Files.newOutputStream(CONFIG)){p.store(out,"Eio Client "+VERSION);}}catch(Exception ignored){}}
  private static final class Mod{final String name,category,description;boolean enabled;int key;Mod(String n,String c,String d,int k){name=n;category=c;description=d;key=k;}}

  public static final class ClickGui extends Screen{
    private static final String[] CATS={"Combat","Movement","Render","Misc"};
    private String selected="Combat";private Mod selectedMod;private Mod listening;private final Map<Integer,Boolean> listenPrev=new HashMap<>();
    ClickGui(){super(Component.literal("Eio Client"));}
    @Override public boolean isPauseScreen(){return false;}
    @Override public void tick(){super.tick();boolean r=key(GUI_KEY);if(r&&!guiPrev){onClose();return;}guiPrev=r;if(listening!=null)pollBind();}
    private void pollBind(){for(int k=GLFW.GLFW_KEY_SPACE;k<=GLFW.GLFW_KEY_LAST;k++){boolean d=key(k),p=listenPrev.getOrDefault(k,d);listenPrev.put(k,d);if(d&&!p){if(k==GLFW.GLFW_KEY_ESCAPE){listening=null;return;}if(k==GLFW.GLFW_KEY_BACKSPACE||k==GLFW.GLFW_KEY_DELETE){listening.key=-1;listening=null;save();return;}if(k==GUI_KEY)continue;listening.key=k;listening=null;save();return;}}}
    private void startBind(Mod m){listening=m;listenPrev.clear();for(int k=GLFW.GLFW_KEY_SPACE;k<=GLFW.GLFW_KEY_LAST;k++)listenPrev.put(k,key(k));}
    @Override public void extractRenderState(GuiGraphicsExtractor g,int mx,int my,float delta){
      g.fill(0,0,width,height,0x78070A0E);int bw=Math.min(700,width-28),bh=Math.min(410,height-28),x=(width-bw)/2,y=(height-bh)/2;
      g.fill(x,y,x+bw,y+bh,0xF3121720);g.fill(x,y,x+bw,y+30,0xFF171E29);g.fill(x,y,x+2,y+bh,0xFF4D9FCB);
      g.text(font,"Eio",x+14,y+10,0xFF8CCDF2,true);g.text(font,"0.7",x+37,y+10,0xFF687584,false);g.text(font,"Right Shift",x+bw-66,y+10,0xFF596675,false);
      int side=112,cy=y+47;g.fill(x,y+30,x+side,y+bh,0xFF0D1118);
      for(String c:CATS){boolean a=c.equals(selected),h=in(mx,my,x+7,cy-5,side-14,22);if(a||h)g.fill(x+7,cy-5,x+side-7,cy+17,a?0xFF183746:0xFF151C25);g.text(font,c,x+16,cy+2,a?0xFF8CCDF2:0xFFB7C0CA,false);cy+=27;}
      g.text(font,"Made by Eio",x+13,y+bh-17,0xFF71808F,false);
      int lx=x+side+13,ly=y+45,lw=220,ry=ly+8;g.text(font,selected.toUpperCase(Locale.ROOT),lx,ly-8,0xFF738292,false);
      for(Mod m:MODS)if(m.category.equals(selected)){boolean h=in(mx,my,lx,ry,lw,36),ch=m==selectedMod;g.fill(lx,ry,lx+lw,ry+32,ch?0xFF1C3140:(h?0xFF1A222D:0xFF141A22));if(m.enabled)g.fill(lx,ry,lx+3,ry+32,0xFF55B7E8);g.text(font,m.name,lx+9,ry+7,m.enabled?0xFFFFFFFF:0xFFD1D6DC,false);String st=m.enabled?"ON":"OFF";g.text(font,st,lx+lw-font.width(st)-9,ry+7,m.enabled?0xFF66D69B:0xFF66717E,false);String ks=m.key<0?"No bind":"Key "+m.key;g.text(font,ks,lx+9,ry+19,0xFF6E8191,false);ry+=38;}
      int dx=lx+lw+16,dw=x+bw-13-dx;g.fill(dx,ly,dx+dw,y+bh-17,0xFF0F141B);
      if(selectedMod==null){g.text(font,"Select a module",dx+16,ly+17,0xFFDCE4EB,false);g.text(font,"Click to toggle.",dx+16,ly+36,0xFF71808F,false);}else{g.text(font,selectedMod.name,dx+16,ly+17,0xFFFFFFFF,true);g.text(font,selectedMod.description,dx+16,ly+42,0xFFAEB9C4,false);int by=ly+76;g.fill(dx+16,by,dx+dw-16,by+27,selectedMod.enabled?0xFF176B4B:0xFF26303B);g.centeredText(font,selectedMod.enabled?"ENABLED":"DISABLED",dx+dw/2,by+9,0xFFFFFFFF);by+=36;g.fill(dx+16,by,dx+dw-16,by+27,listening==selectedMod?0xFF604B1B:0xFF1B2631);String bt=listening==selectedMod?"PRESS A KEY...":(selectedMod.key<0?"SET KEYBIND":"KEYBIND: "+selectedMod.key);g.centeredText(font,bt,dx+dw/2,by+9,0xFFDCE4EB);}
      super.extractRenderState(g,mx,my,delta);
    }
    @Override public boolean mouseClicked(MouseButtonEvent e,boolean doubled){int bw=Math.min(700,width-28),bh=Math.min(410,height-28),x=(width-bw)/2,y=(height-bh)/2,cy=y+47;for(String c:CATS){if(in(e.x(),e.y(),x+7,cy-5,98,22)){selected=c;selectedMod=null;return true;}cy+=27;}int lx=x+125,ly=y+45,ry=ly+8,lw=220;for(Mod m:MODS)if(m.category.equals(selected)){if(in(e.x(),e.y(),lx,ry,lw,32)){selectedMod=m;if(e.button()==0)toggle(m);return true;}ry+=38;}if(selectedMod!=null){int dx=lx+lw+16,dw=x+bw-13-dx,by=ly+112;if(in(e.x(),e.y(),dx+16,by,dw-32,27)){startBind(selectedMod);return true;}}return super.mouseClicked(e,doubled);}
    private static boolean in(double mx,double my,int x,int y,int w,int h){return mx>=x&&mx<x+w&&my>=y&&my<y+h;}
  }
}
