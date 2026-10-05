pipeline {
    agent any
    triggers { pollSCM('H/5 * * * *') }
    stages {
        stage('Install') {
            steps { sh 'python3 -m pip install -e .' }
        }
        stage('Agent test maintenance') {
            steps {
                sh 'pipeline-agent run --base-ref HEAD~1 --head-ref HEAD'
            }
        }
    }
    post {
        always { archiveArtifacts artifacts: '.pipeline-agent/*.json', allowEmptyArchive: true }
    }
}
