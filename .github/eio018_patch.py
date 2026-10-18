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
                .num("Range", 4.5, 1.0, 6.0, 0.25, "Base distance used when Reach is disabled.")
                .num("FOV", 18.0, 5.0, 90.0, 1.0, "Maximum angle from your crosshair used when selecting a target.")
                .bool("Players", true, "Allow attacks on players.")
                .bool("Mobs", true, "Allow attacks on non-player living entities.")
                .bool("Invisible", false, "Allow attacks on invisible living targets.")
                .bool("Require Attack", false, "Only click while Minecraft's attack key is held.");
        mod("Reach", "Combat", "Extends Eio combat target selection up to ten blocks. Servers may still enforce their own hit distance.", -1)
                .num("Range", 6.0, 3.0, 10.0, 0.25, "Extended Eio target-selection distance in blocks.")
                .bool("Kill Aura", true, "Use Reach range for Kill Aura.")
                .bool("Auto Clicker", true, "Use Reach range for Auto Clicker.");''', 'reach module')

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
        Mod lowHealth = find("Low Health Alert");
        Mod clicker = find("Auto Clicker");
        Mod aura = find("Kill Aura");''', '''        Mod respawn = find("Auto Respawn");
        Mod creative = find("Creative Assist");
        Mod lowHealth = find("Low Health Alert");
        Mod clicker = find("Auto Clicker");
        Mod aura = find("Kill Aura");
        Mod reach = find("Reach");''', 'tick module vars')

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

rep('''                    clickTarget = nearestTarget(mc, clicker.num("Range").value, clicker.num("FOV").value,
                            clicker.bool("Players").value, clicker.bool("Mobs").value, clicker.bool("Invisible").value);''', '''                    clickTarget = nearestTarget(mc, effectiveCombatRange(clicker, reach, "Auto Clicker"), clicker.num("FOV").value,
                            clicker.bool("Players").value, clicker.bool("Mobs").value, clicker.bool("Invisible").value);''', 'clicker nearest reach')

rep('''                Entity target = nearestTarget(mc, aura.num("Range").value, aura.num("FOV").value,
                        aura.bool("Players").value, aura.bool("Mobs").value, aura.bool("Invisible").value);''', '''                Entity target = nearestTarget(mc, effectiveCombatRange(aura, reach, "Kill Aura"), aura.num("FOV").value,
                        aura.bool("Players").value, aura.bool("Mobs").value, aura.bool("Invisible").value);''', 'aura reach')

rep('''        double r = clicker.num("Range").value;
        return mc.player.distanceToSqr(target) <= r * r;
    }

    private static void attack''', '''        double r = effectiveCombatRange(clicker, find("Reach"), "Auto Clicker");
        return mc.player.distanceToSqr(target) <= r * r;
    }

    private static double effectiveCombatRange(Mod base, Mod reach, String consumer) {
        double range = base.num("Range").value;
        if (reach != null && reach.enabled && reach.bool(consumer).value) range = Math.max(range, reach.num("Range").value);
        return Math.max(1.0, Math.min(10.0, range));
    }

    private static void attack''', 'effective reach helper')

rep('''        lowHealthAlerted = false;
        lowHealthCooldown = 0;
    }''', '''        lowHealthAlerted = false;
        lowHealthCooldown = 0;
        creativeAssistWarned = false;
        if (creativeAssistSpeedForced && mc.player != null && !find("Fly").enabled) mc.player.getAbilities().setFlyingSpeed(0.05f);
        creativeAssistSpeedForced = false;
    }''', 'runtime creative cleanup')

# Improve module descriptions to surface the modernized controls.
rep('''mod("Kill Aura", "Combat", "Attacks the nearest allowed living target inside the configured range."''', '''mod("Kill Aura", "Combat", "Attacks the nearest allowed living target; Reach can optionally extend its selection distance."''', 'aura description')

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
