// Step global mavenBuild(goals: 'clean verify') : Maven + JDK des Tools, rapports JUnit publies (slide 15)
def call(Map cfg = [:]) {
  def goals = cfg.goals ?: 'clean verify'
  def mvnHome = tool name: cfg.maven ?: 'maven-3.9', type: 'maven'
  def javaHome = tool name: cfg.jdk ?: 'jdk21', type: 'jdk'
  withEnv(["JAVA_HOME=${javaHome}", "PATH+MAVEN=${mvnHome}/bin"]) {
    sh "mvn -B -ntp ${goals}"
  }
  junit allowEmptyResults: true, testResults: '**/target/surefire-reports/TEST-*.xml'
}
