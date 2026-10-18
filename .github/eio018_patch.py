from pathlib import Path
import json

p=Path('eio26/EioClient.java')
s=p.read_text()

def rep(old,new,label):
    global s
    if old not in s:
        raise SystemExit('patch target not found: '+label)
    s=s.replace(old,new,1)

rep('public static final String VERSION = "0.17.0";', 'public static final String VERSION = "0.18.0";', 'version')
rep('public static final String BUILD_ID = "EIO-017-QA1";', 'public static final String BUILD_ID = "EIO-018-QA1";', 'build id')

rep('''        mod("Auto Clicker", "Combat", "Automatically attacks a valid target near your crosshair at the configured rate.", InputConstants.KEY_C)
                .num("CPS", 10.0, 1.0, 20.0, 1.0, "Attack attempts per second.")
                .num("Range", 4.5, 1.0, 6.0, 0.25, "Maximum distance used when selecting a click target.")
                .num("FOV", 18.0, 5.0, 90.0, 1.0, "Maximum angle from your crosshair used when selecting a target.")
                .bool("Players", true, "Allow attacks on players.")
                .bool("Mobs", true, "Allow attacks on non-player living entities.")
                .bool("Invisible", false, "Allow attacks on invisible living targets.")
                .bool("Require Attack", false, "Only click while Minecraft's attack key is held.");''', '''        mod("Auto Clicker", "Combat", "Automatically attacks a valid target near your crosshair at the configured rate.", InputConstants.KEY_C)
                .num("CPS", 10.0, 1.0, 20.0, 1.0, "Attack attempts per second.")
                .num("Range", 4.5, 1.0, 6.0, 0.25, "Maximum distance used when selecting a click target.")
                .num("FOV", 18.0, 5.0, 90.0, 1.0, "Maximum angle from your crosshair used when selecting a target.")
                .bool("Players", true, "Allow attacks on players.")
                .bool("Mobs", true, "Allow attacks on non-player living entities.")
                .bool("Invisible", false, "Allow attacks on invisible living targets.")
                .bool("Require Attack", false, "Only click while Minecraft's attack key is held.");
        mod("Reach", "Combat", "Shows the nearest allowed target inside a configurable 3-10 block radius without changing server hit distance.", -1)
                .num("Range", 6.0, 3.0, 10.0, 0.25, "Target scan and display radius in blocks.")
                .bool("Players", true, "Include players in Reach display targeting.")
                .bool("Mobs", true, "Include non-player living entities in Reach display targeting.")
                .bool("Invisible", false, "Include invisible living entities in Reach display targeting.");''', 'reach module')

rep('''        mod("Auto Respawn", "Player", "Automatically respawns after death.", -1);''', '''        mod("Auto Respawn", "Player", "Automatically respawns after death.", -1);
        mod("Creative Assist", "Player", "Creative-flight helper that activates only when the server/player already grants flight permission.", -1)
                .bool("Auto Fly", true, "Automatically enter flight while creative flight permission is available.")
                .num("Flight Speed", 0.10, 0.05, 1.00, 0.05, "Creative flight speed while this helper is active.");''', 'creative module')

rep('''    private static boolean lowHealthAlerted;
    private static int lowHealthCooldown;''', '''    private static boolean lowHealthAlerted;
    private static int lowHealthCooldown;
    private static boolean creativeAssistWarned;
    private static boolean creativeAssistSpeedForced;''', 'creative state')

rep('''        Mod respawn = find("Auto Respawn");
        Mod lowHealth = find("Low Health Alert");''', '''        Mod respawn = find("Auto Respawn");
        Mod creative = find("Creative Assist");
        Mod lowHealth = find("Low Health Alert");''', 'creative tick var')

rep('''        if (respawn.enabled && mc.player.isDeadOrDying()) mc.player.respawn();

        if (lowHealth.enabled) {''', '''        if (respawn.enabled && mc.player.isDeadOrDying()) mc.player.respawn();

        if (creative.enabled && !fly.enabled && creative.bool("Auto Fly").value) {
            var abilities = mc.player.getAbilities();
            if (abilities.mayfly) {
                abilities.flying = true;
                abilities.setFlyingSpeed((float) creative.num("Flight Speed").value);
                creativeAssistSpeedForced = true;
                creativeAssistWarned = false;
            } else if (!creativeAssistWarned) {
                notifyMessage("CREATIVE ASSIST: SERVER FLIGHT PERMISSION REQUIRED", 0xFFFFB36B, 3200L);
                creativeAssistWarned = true;
            }
        } else {
            creativeAssistWarned = false;
            if (creativeAssistSpeedForced && !fly.enabled) {
                mc.player.getAbilities().setFlyingSpeed(0.05f);
                creativeAssistSpeedForced = false;
            }
        }

        if (lowHealth.enabled) {''', 'creative tick')

rep('''        lowHealthAlerted = false;
        lowHealthCooldown = 0;
    }''', '''        lowHealthAlerted = false;
        lowHealthCooldown = 0;
        creativeAssistWarned = false;
        if (creativeAssistSpeedForced && mc.player != null && !find("Fly").enabled) mc.player.getAbilities().setFlyingSpeed(0.05f);
        creativeAssistSpeedForced = false;
    }''', 'creative cleanup')

# Add Reach readout ahead of Target HUD.
rep('''        if (find("Target HUD").enabled) {
            Entity t = followTarget;''', '''        if (find("Reach").enabled) {
            Mod reach = find("Reach");
            Entity rt = nearestTarget(mc, reach.num("Range").value, 360.0,
                    reach.bool("Players").value, reach.bool("Mobs").value, reach.bool("Invisible").value);
            if (rt != null) {
                double rd = Math.sqrt(mc.player.distanceToSqr(rt));
                g.text(mc.font, "Reach " + rt.getDisplayName().getString() + " " + String.format(Locale.ROOT, "%.1fm", rd), 5, y, 0xFF9DD9FF, true);
                y += 11;
            }
        }
        if (find("Target HUD").enabled) {
            Entity t = followTarget;''', 'reach hud')

p.write_text(s)

gp=Path('gradle.properties')
g=gp.read_text()
if 'mod_version=0.17.0+26.3' not in g: raise SystemExit('gradle version target missing')
gp.write_text(g.replace('mod_version=0.17.0+26.3','mod_version=0.18.0+26.3',1))

lang_path=Path('src/main/resources/assets/eioclient/lang/en_us.json')
lang=json.loads(lang_path.read_text())
lang['key.eioclient.reach']='Reach'
lang['key.eioclient.creative_assist']='Creative Assist'
lang_path.write_text(json.dumps(lang,indent=2)+'\n')
