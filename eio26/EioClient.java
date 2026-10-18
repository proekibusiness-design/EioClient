package com.eio.client;

import com.mojang.blaze3d.platform.InputConstants;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.fabricmc.api.ClientModInitializer;
import net.fabricmc.fabric.api.client.command.v2.*;
import net.fabricmc.fabric.api.client.event.lifecycle.v1.ClientTickEvents;
import net.fabricmc.fabric.api.client.keymapping.v1.KeyMappingHelper;
import net.fabricmc.fabric.api.client.rendering.v1.hud.HudElementRegistry;
import net.minecraft.client.*;
import net.minecraft.client.gui.GuiGraphicsExtractor;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.input.MouseButtonEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import java.util.*;

public final class EioClient implements ClientModInitializer {
  public static final String VERSION="0.6.1";
  private static final List<Mod> MODS=new ArrayList<>();
  private static KeyMapping guiKey;
  private static boolean guiWasDown;

  static {
    add("Kill Aura","Combat","Automatically attacks nearby targets. No bypass or evasion logic.",false);
    add("Auto Clicker","Combat","Automatically repeats attacks while the attack key is held.",false);
    add("Sprint","Movement","Automatically sprints while moving forward.",true);
    add("AutoWalk","Movement","Keeps the forward key held for you.",true);
    add("Fly","Movement","Client flight movement module.",false);
    add("SafeWalk","Movement","Movement utility.",false);
    add("Coordinates","Render","Shows your XYZ position.",true);
    add("FPS","Render","Shows current FPS.",true);
    add("Active Modules","Render","Shows enabled modules.",true);
    add("Fullbright","Render","Brightness utility.",false);
    add("Auto Respawn","Player","Player convenience module.",false);
    add("Inventory Info","Player","Inventory information.",false);
    add("Durability HUD","Player","Equipment durability information.",false);
    add("Waypoints","World","Navigation utility.",false);
    add("Chunk Info","World","Chunk information.",false);
    add("Session Info","Misc","Session information.",true);
    add("Notifications","Misc","Module state indicator.",true);
  }

  private static void add(String n,String c,String d,boolean ready){MODS.add(new Mod(n,c,d,ready));}

  @Override public void onInitializeClient(){
    KeyMapping.Category cat=KeyMapping.Category.register(Identifier.fromNamespaceAndPath("eioclient","general"));
    guiKey=KeyMappingHelper.registerKeyMapping(new KeyMapping("key.eioclient.clickgui",InputConstants.Type.KEYBOARD,344,cat));
    ClientTickEvents.END_CLIENT_TICK.register(EioClient::tick);
    HudElementRegistry.addLast(Identifier.fromNamespaceAndPath("eioclient","hud"),EioClient::hud);
    ClientCommandRegistrationCallback.EVENT.register((d,a)->d.register(ClientCommands.literal("eio")
      .executes(c->{openGui();return 1;})
      .then(ClientCommands.literal("gui").executes(c->{openGui();return 1;}))
      .then(ClientCommands.literal("list").executes(c->{c.getSource().sendFeedback(Component.literal(summary()));return 1;}))
      .then(ClientCommands.literal("toggle").then(ClientCommands.argument("module",StringArgumentType.greedyString()).executes(c->{Mod m=find(StringArgumentType.getString(c,"module"));if(m==null){c.getSource().sendFeedback(Component.literal("Unknown module"));return 0;}toggle(m);return 1;})))));
  }

  private static void openGui(){ Minecraft.getInstance().setScreenAndShow(new ClickGui()); }

  private static void tick(Minecraft mc){
    boolean down=guiKey!=null&&guiKey.isDown();
    if(down&&!guiWasDown) openGui();
    guiWasDown=down;
    if(mc.player==null)return;
    Mod w=find("AutoWalk"),s=find("Sprint");
    if(w.enabled)mc.options.keyUp.setDown(true);
    if(s.enabled&&mc.options.keyUp.isDown()&&mc.player.getFoodData().getFoodLevel()>6&&!mc.player.horizontalCollision)mc.player.setSprinting(true);
  }

  private static void hud(GuiGraphicsExtractor g,DeltaTracker dt){
    Minecraft mc=Minecraft.getInstance();if(mc.player==null)return;
    int y=5;g.text(mc.font,"Eio",5,y,0xFF8CCDF2,true);y+=11;
    if(find("Coordinates").enabled){g.text(mc.font,String.format(Locale.ROOT,"XYZ %.1f  %.1f  %.1f",mc.player.getX(),mc.player.getY(),mc.player.getZ()),5,y,0xFFD9E0E6,true);y+=11;}
    if(find("FPS").enabled){g.text(mc.font,"FPS "+mc.getFps(),5,y,0xFFD9E0E6,true);y+=11;}
    if(find("Active Modules").enabled)for(Mod m:MODS)if(m.enabled&&!m.name.equals("Active Modules")&&!m.name.equals("Coordinates")&&!m.name.equals("FPS")){g.text(mc.font,m.name,5,y,0xFF91BDD8,true);y+=10;}
  }

  private static Mod find(String n){for(Mod m:MODS)if(m.name.equalsIgnoreCase(n))return m;return null;}
  private static void toggle(Mod m){m.enabled=!m.enabled;if(m.name.equals("AutoWalk")&&!m.enabled)Minecraft.getInstance().options.keyUp.setDown(false);}
  private static String summary(){StringJoiner j=new StringJoiner(" | ");for(Mod m:MODS)j.add(m.name+":"+(m.enabled?"ON":"OFF"));return j.toString();}
  private static final class Mod{final String name,category,description;final boolean ready;boolean enabled;Mod(String n,String c,String d,boolean r){name=n;category=c;description=d;ready=r;}}

  public static final class ClickGui extends Screen{
    private static final String[] CATS={"Combat","Movement","Render","Player","World","Misc"};
    private String selected="Combat";private Mod selectedMod;
    ClickGui(){super(Component.literal("Eio Client"));}
    @Override public boolean isPauseScreen(){return false;}
    @Override public void extractRenderState(GuiGraphicsExtractor g,int mx,int my,float delta){
      g.fill(0,0,width,height,0x9A080B10);int bw=Math.min(720,width-30),bh=Math.min(430,height-30),x=(width-bw)/2,y=(height-bh)/2;
      g.fill(x,y,x+bw,y+bh,0xF0121720);g.fill(x,y,x+bw,y+32,0xFF171E29);g.fill(x,y,x+3,y+bh,0xFF4D9FCB);
      g.text(font,"Eio",x+15,y+11,0xFF8CCDF2,true);g.text(font,"26.3",x+38,y+11,0xFF7A8794,false);g.text(font,"RShift",x+bw-47,y+11,0xFF596675,false);
      int side=120,cy=y+48;g.fill(x,y+32,x+side,y+bh,0xFF0D1118);
      for(String c:CATS){boolean a=c.equals(selected),h=in(mx,my,x+8,cy-5,side-16,23);if(a||h)g.fill(x+8,cy-5,x+side-8,cy+18,a?0xFF183746:0xFF151C25);g.text(font,c,x+18,cy+3,a?0xFF8CCDF2:0xFFB7C0CA,false);cy+=28;}
      g.text(font,"Made by Eio",x+15,y+bh-18,rainbow(),false);
      int lx=x+side+14,ly=y+46,lw=220,ry=ly+8;g.text(font,selected.toUpperCase(Locale.ROOT),lx,ly-8,0xFF738292,false);
      for(Mod m:MODS)if(m.category.equals(selected)){boolean h=in(mx,my,lx,ry,lw,38),ch=m==selectedMod;g.fill(lx,ry,lx+lw,ry+34,ch?0xFF1C3140:(h?0xFF1A222D:0xFF141A22));if(m.enabled)g.fill(lx,ry,lx+3,ry+34,0xFF55B7E8);g.text(font,m.name,lx+10,ry+7,m.enabled?0xFFFFFFFF:0xFFD1D6DC,false);String st=m.enabled?"ON":"OFF";g.text(font,st,lx+lw-font.width(st)-9,ry+7,m.enabled?0xFF66D69B:0xFF66717E,false);g.text(font,m.ready?"Ready":"Experimental",lx+10,ry+20,m.ready?0xFF6E8191:0xFF806D72,false);ry+=40;}
      int dx=lx+lw+18,dw=x+bw-14-dx;g.fill(dx,ly,dx+dw,y+bh-18,0xFF0F141B);
      if(selectedMod==null){g.text(font,"Select a module",dx+18,ly+18,0xFFDCE4EB,false);g.text(font,"Left click toggles it.",dx+18,ly+38,0xFF71808F,false);}else{g.text(font,selectedMod.name,dx+18,ly+18,0xFFFFFFFF,true);g.text(font,selectedMod.category,dx+18,ly+34,0xFF8CCDF2,false);g.text(font,selectedMod.description,dx+18,ly+60,0xFFAEB9C4,false);int by=ly+92;g.fill(dx+18,by,dx+dw-18,by+28,selectedMod.enabled?0xFF176B4B:0xFF26303B);g.centeredText(font,selectedMod.enabled?"ENABLED":"DISABLED",dx+dw/2,by+10,0xFFFFFFFF);}
      super.extractRenderState(g,mx,my,delta);
    }
    @Override public boolean mouseClicked(MouseButtonEvent e,boolean doubled){int bw=Math.min(720,width-30),bh=Math.min(430,height-30),x=(width-bw)/2,y=(height-bh)/2,cy=y+48;for(String c:CATS){if(in(e.x(),e.y(),x+8,cy-5,104,23)){selected=c;selectedMod=null;return true;}cy+=28;}int lx=x+134,ry=y+54,lw=220;for(Mod m:MODS)if(m.category.equals(selected)){if(in(e.x(),e.y(),lx,ry,lw,34)){selectedMod=m;if(e.button()==0)toggle(m);return true;}ry+=40;}return super.mouseClicked(e,doubled);}
    private static int rainbow(){float h=(System.currentTimeMillis()%7000L)/7000f;return 0xFF000000|java.awt.Color.HSBtoRGB(h,.42f,1f);}
    private static boolean in(double mx,double my,int x,int y,int w,int h){return mx>=x&&mx<x+w&&my>=y&&my<y+h;}
  }
}
