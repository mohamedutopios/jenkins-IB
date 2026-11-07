// Mise en etat "fin de partie 1" (execute une fois par init.groovy.d, puis supprime par etat-partie1.sh).
// Les secrets sont deposes par le script shell dans JENKINS_HOME/etat-partie1/ et effaces ensuite.
import jenkins.model.Jenkins
import jenkins.model.JenkinsLocationConfiguration
import hudson.security.HudsonPrivateSecurityRealm
import hudson.security.FullControlOnceLoggedInAuthorizationStrategy
import hudson.model.JDK
import hudson.tasks.Maven
import hudson.tools.InstallSourceProperty
import hudson.slaves.DumbSlave
import hudson.slaves.RetentionStrategy
import hudson.model.Node
import com.cloudbees.plugins.credentials.CredentialsScope
import com.cloudbees.plugins.credentials.SystemCredentialsProvider
import com.cloudbees.plugins.credentials.domains.Domain
import com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl
import com.cloudbees.jenkins.plugins.sshcredentials.impl.BasicSSHUserPrivateKey
import hudson.plugins.sshslaves.SSHLauncher
import hudson.plugins.sshslaves.verifiers.NonVerifyingKeyVerificationStrategy
import org.jenkinsci.plugins.configfiles.GlobalConfigFiles
import org.jenkinsci.plugins.configfiles.maven.MavenSettingsConfig

def j = Jenkins.get()
def dir = new File(j.rootDir, 'etat-partie1')
def lire = { String nom -> new File(dir, nom).text.trim() }

// Demo 1 : administrateur, autorisation par defaut, interface en anglais
def realm = new HudsonPrivateSecurityRealm(false)
def admin = realm.createAccount('admin', 'Formation-2026')
admin.fullName = 'Administrateur Jenkins'
admin.addProperty(new hudson.tasks.Mailer.UserProperty('admin@example.com'))
admin.save()
j.securityRealm = realm
def autorisation = new FullControlOnceLoggedInAuthorizationStrategy()
autorisation.allowAnonymousRead = false
j.authorizationStrategy = autorisation
def locale = hudson.plugins.locale.PluginImpl.get()
locale.systemLocale = 'en'
locale.ignoreAcceptLanguage = true
locale.save()

// Demo 5 : reglages System, controller sans executor
j.systemMessage = 'Jenkins de formation - demos library (partie 2)'
j.numExecutors = 0
j.scmCheckoutRetryCount = 2
def location = JenkinsLocationConfiguration.get()
location.url = 'http://localhost:8080/'
location.adminAddress = 'jenkins@example.com'
location.save()

// Demo 7 : outils
j.getDescriptorByType(JDK.DescriptorImpl).setInstallations(new JDK('jdk21', '/opt/java/openjdk'))
def maven = new Maven.MavenInstallation('maven-3.9', null,
    [new InstallSourceProperty([new Maven.MavenInstaller('3.9.16')])])
j.getDescriptorByType(Maven.DescriptorImpl).setInstallations(maven)

// Demos 5, 7, 14 : credentials
def store = SystemCredentialsProvider.instance.store
store.addCredentials(Domain.global(), new BasicSSHUserPrivateKey(CredentialsScope.SYSTEM, 'agent-ssh-key', 'jenkins',
    new BasicSSHUserPrivateKey.DirectEntryPrivateKeySource(lire('jenkins_agent')), null, 'Cle du controller pour les agents SSH'))
store.addCredentials(Domain.global(), new UsernamePasswordCredentialsImpl(CredentialsScope.GLOBAL, 'gitea-token',
    'Gitea - jeton lecture', 'formation', lire('gitea-token')))
store.addCredentials(Domain.global(), new UsernamePasswordCredentialsImpl(CredentialsScope.GLOBAL, 'nexus-deploy',
    'Nexus - publication Maven', 'jenkins', 'Jenkins-2026'))

// Demo 5 : agent SSH linux-1
def launcher = new SSHLauncher('linux-1', 22, 'agent-ssh-key')
launcher.sshHostKeyVerificationStrategy = new NonVerifyingKeyVerificationStrategy()
def agent = new DumbSlave('linux-1', '/home/jenkins/agent', launcher)
agent.nodeDescription = 'Agent Linux JDK 21 (conteneur linux-1)'
agent.numExecutors = 2
agent.labelString = 'linux java21 maven docker'
agent.mode = Node.Mode.EXCLUSIVE
agent.retentionStrategy = RetentionStrategy.Always.INSTANCE
j.addNode(agent)

// Demo 13 : SMTP vers Mailpit
def mailer = j.getDescriptorByType(hudson.tasks.Mailer.DescriptorImpl)
mailer.smtpHost = 'mailpit'
mailer.smtpPort = '1025'
mailer.save()
def emailext = j.getDescriptorByType(hudson.plugins.emailext.ExtendedEmailPublisherDescriptor)
emailext.mailAccount.smtpHost = 'mailpit'
emailext.mailAccount.smtpPort = '1025'
emailext.defaultContentType = 'text/html'
emailext.defaultRecipients = 'dev-team@example.com'
emailext.save()

// Demo 14 : settings.xml gere (nexus-public sert a lire les SNAPSHOT de la partie 2)
def serveur = { String id -> """    <server>
      <id>${id}</id>
      <username>\${env.NEXUS_USR}</username>
      <password>\${env.NEXUS_PSW}</password>
    </server>""" }
def settings = "<settings>\n  <servers>\n${['nexus-releases', 'nexus-snapshots', 'nexus-public'].collect(serveur).join('\n')}\n  </servers>\n</settings>\n"
GlobalConfigFiles.get().save(new MavenSettingsConfig('nexus-settings', 'nexus-settings', 'Publication et lecture Nexus', settings, false, null))

j.save()
println 'etat-partie1 : configuration appliquee'
