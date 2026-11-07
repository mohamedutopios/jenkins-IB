// Job DSL (slide 56) : les jobs et les vues de la suite Library decrits en code
folder('library-dsl') {
  description('Jobs generes par le seed job : ne pas modifier a la main')
}

pipelineJob('library-dsl/library-core') {
  description('Genere par Job DSL')
  definition {
    cpsScm {
      scm {
        git {
          remote { url('http://gitea:3000/formation/library-core.git'); credentials('gitea-token') }
          branch('*/main')
        }
      }
      scriptPath('Jenkinsfile')
      lightweight(true)
    }
  }
}

pipelineJob('library-dsl/library-legacy') {
  description('Genere par Job DSL')
  definition {
    cpsScm {
      scm {
        git {
          remote { url('http://gitea:3000/formation/library-legacy.git'); credentials('gitea-token') }
          branch('*/main')
        }
      }
      scriptPath('Jenkinsfile')
      lightweight(true)
    }
  }
}

listView('Library DSL') {
  description('Vue generee par Job DSL')
  jobs { regex('library-dsl/.*') }
  recurse(true)
  columns { status(); weather(); name(); lastSuccess(); lastFailure(); lastDuration(); buildButton() }
}
