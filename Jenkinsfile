pipeline {
    agent any

    environment {
        DOCKERHUB_CREDENTIALS = 'docker-hub-credentials'
        IMAGE_NAME            = 'jaeyoungkimdockerhub/fastapi-app'
        REMOTE_USER           = 'sogang018'
        REMOTE_HOST           = '163.239.77.78'
        REMOTE_PATH           = '/home/sogang018@SGVDI.local/20221543'
        COMPOSE_FILE          = 'docker-compose.yml'
        SONAR_TOKEN           = credentials('sonar-token')
        SONAR_HOST_URL        = 'http://localhost:9000'
        JMETER_IMAGE_NAME     = 'my-arm-jmeter'
    }

    stages {
        stage('Checkout') {
            steps {
                git url: 'https://github.com/Gnomonn/CSE4022-FastApi-Todos', branch: 'main'
            }
        }

        stage('Setup Environment & Install Dependencies') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate                   
                    pip install -r FastApi_Todos/fastapi-app/requirements.txt             
                '''
            }
        }

        stage('Test & Coverage') {
            steps {
                sh '''
                    . venv/bin/activate
                    
                    cd FastApi_Todos/fastapi-app
                    mkdir -p pytest_report
                    
                    pytest tests/test_main.py \\
                        --html=pytest_report/report.html \\
                        --self-contained-html \\
                        --cov=. \\
                        --cov-report=xml:coverage.xml \\
                        --cov-report=html:htmlcov
                        
                    cd ../..
                    cp FastApi_Todos/fastapi-app/coverage.xml . || true
                    mkdir -p pytest_report htmlcov
                    cp FastApi_Todos/fastapi-app/pytest_report/report.html pytest_report/ || true
                    cp -r FastApi_Todos/fastapi-app/htmlcov/* htmlcov/ || true
                '''
            }
            post {
                always {
                    publishHTML(target: [
                        reportName           : 'Pytest HTML Report', 
                        reportDir            : 'pytest_report',
                        reportFiles          : 'report.html',
                        keepAll              : true,
                        alwaysLinkToLastBuild: true,
                        allowMissing         : true
                    ])
                    publishHTML(target: [
                        reportName           : 'Coverage Report', 
                        reportDir            : 'htmlcov',
                        reportFiles          : 'index.html',
                        keepAll              : true,
                        alwaysLinkToLastBuild: true,
                        allowMissing         : true
                    ])
                    archiveArtifacts artifacts: 'pytest_report/**/*, htmlcov/**/*, coverage.xml', allowEmptyArchive: true
                }
            }
        }

        stage('Build') {
            steps {
                dir('FastApi_Todos/fastapi-app') {
                    script {
                        docker.build("${IMAGE_NAME}:latest", ".")
                    }
                }
            }
        }

        stage('Push') {
            steps {
                script {
                    docker.withRegistry('https://index.docker.io/v1/', DOCKERHUB_CREDENTIALS) {
                        docker.image("${IMAGE_NAME}:latest").push()
                    }
                }
            }
        }

        stage('Deploy') {
            steps {
                script {
                    sshagent(credentials: ['team']) {
                    sh """
                    ssh -o StrictHostKeyChecking=no ${REMOTE_USER}@${REMOTE_HOST} << EOF
                        docker pull ${IMAGE_NAME}:latest
                        
                        # 기존 FastAPI 컨테이너 정리
                        docker stop FastApi-app || true
                        docker rm FastApi-app || true
                        
                        # 기존 InfluxDB 컨테이너 정리 (추가)
                        docker stop influxdb || true
                        docker rm influxdb || true
                        
                        # InfluxDB 컨테이너 실행 (추가)
                        docker run -d --name influxdb -p 8086:8086 \\
                            -e DOCKER_INFLUXDB_INIT_MODE=setup \\
                            -e DOCKER_INFLUXDB_INIT_USERNAME=admin \\
                            -e DOCKER_INFLUXDB_INIT_PASSWORD=password123 \\
                            -e DOCKER_INFLUXDB_INIT_ORG=my-org \\
                            -e DOCKER_INFLUXDB_INIT_BUCKET=jmeter-bucket \\
                            -e DOCKER_INFLUXDB_INIT_ADMIN_TOKEN=my-super-secret-auth-token \\
                            influxdb:latest
                        
                        # FastAPI 앱 실행
                        docker run -d --name FastApi-app -p 8003:8000 ${IMAGE_NAME}:latest
                        exit
EOF
                    """
                    }
                }
            }
        }

        stage('Build JMeter Image') {
            steps {
                dir('FastApi_Todos/jmeter') {
                    script {
                        docker.build("${JMETER_IMAGE_NAME}:latest", ".")
                    }
                }
            }
        }

        stage('Run JMeter Load Test') {
            steps {
                sh '''
                    BASE_DIR="$WORKSPACE/FastApi_Todos/jmeter"
                    rm -rf "$BASE_DIR/report" "$BASE_DIR/jmeter.log" "$BASE_DIR/results.jtl"
                    
                    TARGET_URL="http://${REMOTE_HOST}:8003"
                    
                    CONTAINER_ID=\$(docker create --network host --user root:root ${JMETER_IMAGE_NAME}:latest \\
                        sh -c "jmeter -n -t fastapi_test_plan.jmx -JBASE_URL=\$TARGET_URL -l results.jtl -Jjmeter.save.saveservice.output_format=csv -e -o report")
                    
                    docker cp "$BASE_DIR"/*.jmx \$CONTAINER_ID:/opt/apache-jmeter-5.4.1/fastapi_test_plan.jmx
                    docker start -a \$CONTAINER_ID || true
                    
                    docker cp \$CONTAINER_ID:/opt/apache-jmeter-5.4.1/report "$BASE_DIR/" || true
                    docker cp \$CONTAINER_ID:/opt/apache-jmeter-5.4.1/results.jtl "$BASE_DIR/" || true
                    docker rm \$CONTAINER_ID
                '''
            }
            post {
                always {
                    publishHTML(target: [
                        reportName           : 'JMeter HTML Report',
                        reportDir            : 'FastApi_Todos/jmeter/report',
                        reportFiles          : 'index.html',
                        keepAll              : true,
                        alwaysLinkToLastBuild: true,
                        allowMissing         : true
                    ])
                    archiveArtifacts artifacts: 'FastApi_Todos/jmeter/report/**/*, FastApi_Todos/jmeter/results.jtl', allowEmptyArchive: true
                }
            }
        }
    }

    post {
        always {
            echo 'Pipeline completed.'
        }
    }
}
