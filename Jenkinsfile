pipeline {
    agent any
    options {
        timeout(time: 1, unit: 'HOURS')
    }
    parameters {
        string(name: 'PERSON', defaultValue: 'Mr Jenkins', description: 'Who should I say hello to?')
    }
    environment {
        DISABLE_AUTH = 'true'
        DB_ENGINE    = 'sqlite'
    }
    stages {
        stage('Build') {
            steps {
                checkout([$class: 'GitSCM', branches: [[name: '*/master'], [name: '*/develop']], doGenerateSubmoduleConfigurations: false, extensions: [], submoduleCfg: [], userRemoteConfigs: [[credentialsId: 'ddb2c5d8-aa15-4608-aca1-44c5e3558a5d', url: 'https://github.com/lrbsunday/distsuper']]])
            }
        }
        stage('Test') {
            steps {
                echo 'Testing'
                sh 'virtualenv venv && . venv/bin/activate && pip install pylint pytest\\<4 pytest-allure-adaptor pytest-cov'
                sh '. venv/bin/activate && py.test --verbose --junit-xml test-reports/results.xml --cov-report=html --cov=distsuper --alluredir allure-results test.py || exit 0'
                sh '. venv/bin/activate && pylint --output-format=parseable distsuper > pylint.xml || exit 0'
            }
            post {
                always {
                    junit 'test-reports/results.xml'
                    allure includeProperties: false, jdk: '', results: [[path: 'allure-results']]
                    publishHTML([allowMissing: false, alwaysLinkToLastBuild: false, keepAll: true, reportDir: 'htmlcov', reportFiles: 'index.html', reportName: '代码覆盖率', reportTitles: '代码覆盖率'])
                }
            }
        }
        stage('Confirm') {
            steps {
                input "Does the staging environment look ok?"
            }
        }
        stage('Deploy - not run') {
            when {
                branch 'production'
            }
            steps {
                echo 'Deploying'
            }
        }
        stage('Deploy') {
            steps {
                echo 'Deploying'
            }
        }
    }
    post {
        always {

            echo 'This will always run'
        }
        success {
            echo 'This will run only if successful'
        }
        failure {
            echo 'This will run only if failed'
        }
        unstable {
            echo 'This will run only if the run was marked as unstable'
        }
        changed {
            echo 'This will run only if the state of the Pipeline has changed'
            echo 'For example, if the Pipeline was previously failing but is now successful'
        }
    }
}