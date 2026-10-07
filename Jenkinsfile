pipeline {
    agent any

    options {
        timeout(time: 10, unit: 'MINUTES')
        disableConcurrentBuilds()
        timestamps()
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    stages {
        stage('Environment') {
            steps {
                sh '''
                    python3 --version
                    python3 -m venv .venv
                    .venv/bin/python -m pip install --upgrade pip
                    .venv/bin/python -m pip install -e ".[test]"
                '''
            }
        }

        stage('Test') {
            steps {
                sh '''
                    mkdir -p reports
                    .venv/bin/python -m pytest tests -q --junitxml=reports/junit.xml
                '''
            }
        }
    }

    post {
        always {
            junit testResults: 'reports/junit.xml', allowEmptyResults: true
            archiveArtifacts artifacts: 'reports/junit.xml', allowEmptyArchive: true
        }
    }
}
