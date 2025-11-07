pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'registry-harbor.yafex.cn/dev/'
        PROJECT_NAME = 'easytesting'
        DOCKER_IMAGE = "${DOCKER_REGISTRY}/${PROJECT_NAME}:${BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: 'master',
                    url: 'https://gitee.com/joyamon/easy-testing.git',
                    credentialsId: '8d3f60f0-9b76-013e-6058-3efc22a1eea9'
            }
        }

        stage('Test') {
            parallel {
                stage('Unit Tests') {
                    steps {
                        sh '''
                            docker build -t ${PROJECT_NAME}-test .
                            docker run --rm ${PROJECT_NAME}-test python manage.py test
                        '''
                    }
                }
                stage('Static Analysis') {
                    steps {
                        sh '''
                            docker run --rm -v $(pwd):/app python:3.9-slim \
                            pip install flake8 && flake8 .
                        '''
                    }
                }
                stage('Security Scan') {
                    steps {
                        sh '''
                            docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
                            aquasec/trivy image --exit-code 1 ${PROJECT_NAME}-test
                        '''
                    }
                }
            }
        }

        stage('Build') {
            steps {
                script {
                    sh "docker build -t ${DOCKER_IMAGE} ."
                }
            }
        }

        stage('Push to Registry') {
            steps {
                script {
                    withCredentials([usernamePassword(
                        credentialsId: 'harbor-credentials',
                        usernameVariable: 'zhouyanming',
                        passwordVariable: 'zym12345678'
                    )]) {
                        sh """
                            docker login -u ${DOCKER_USER} -p ${DOCKER_PASS} ${DOCKER_REGISTRY}
                            docker push ${DOCKER_IMAGE}
                        """
                    }
                }
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                    scp -o StrictHostKeyChecking=no \
                        docker-compose.yml \
                        nginx.conf \
                        deploy-user@staging-server:/opt/easytesting/

                    ssh deploy-user@staging-server \
                        "cd /opt/easytesting && \
                         docker-compose pull && \
                         docker-compose up -d && \
                         ./scripts/health_check.sh"
                '''
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'master'
            }
            steps {
                input message: 'Deploy to production?', ok: 'Deploy'
                sh '''
                    scp -o StrictHostKeyChecking=no \
                        docker-compose.yml \
                        nginx.conf \
                        deploy-user@production-server:/opt/easytesting/

                    ssh deploy-user@production-server \
                        "cd /opt/easytesting && \
                         docker-compose pull && \
                         docker-compose up -d && \
                         ./scripts/health_check.sh"
                '''
            }
        }
    }

    post {
        always {
            // 清理工作
            sh 'docker system prune -f'
            // 发送通知
            emailext (
                subject: "Build ${currentBuild.result}: Job ${env.JOB_NAME}",
                body: "Build URL: ${env.BUILD_URL}",
                to: "dev-team@yourcompany.com"
            )
        }
        success {
            slackSend channel: '#deployments',
                     message: "EasyTesting部署成功: ${env.BUILD_URL}"
        }
        failure {
            slackSend channel: '#deployments',
                     message: "EasyTesting部署失败: ${env.BUILD_URL}"
        }
    }
}