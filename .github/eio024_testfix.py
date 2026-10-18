from pathlib import Path

p = Path('build.gradle')
s = p.read_text()

# Gradle 9.6 requires the Platform launcher on the test runtime classpath.
if 'testRuntimeOnly "org.junit.platform:junit-platform-launcher"' not in s:
    needle = '    testImplementation "org.junit.jupiter:junit-jupiter"\n'
    if needle not in s:
        raise SystemExit('JUnit Jupiter dependency not found')
    s = s.replace(needle, needle + '    testRuntimeOnly "org.junit.platform:junit-platform-launcher"\n', 1)

# Avoid Task.project access at processResources execution time (deprecated in Gradle 9, error in Gradle 10).
old = '''processResources {
    inputs.property 'version', project.version
    filesMatching('fabric.mod.json') {
        expand version: project.version
    }
}'''
new = '''def modVersion = project.version
processResources {
    inputs.property 'version', modVersion
    filesMatching('fabric.mod.json') {
        expand version: modVersion
    }
}'''
if old in s:
    s = s.replace(old, new, 1)
elif 'def modVersion = project.version' not in s:
    raise SystemExit('unexpected processResources configuration')

p.write_text(s)
