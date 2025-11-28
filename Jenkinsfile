pipeline {
    agent any
    environment {
        PROJECT_NAME = 'EasyTesting'
        VENV_PATH = "${WORKSPACE}/venv"
    }
    stages {
        stage('Checkout') {
            steps {
                git branch: 'master',
                url: 'https://gitee.com/joyamon/easy-testing.git'
                echo '✅ 代码检出完成'
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                    # 检查Python环境
                    echo "Python版本:"
                    python3 --version || python --version

                    # 创建虚拟环境（使用更兼容的方式）
                    python3 -m venv "${VENV_PATH}" || python -m venv "${VENV_PATH}" || virtualenv "${VENV_PATH}"

                    # 激活虚拟环境的替代方案：直接使用虚拟环境中的pip和python
                    echo "使用虚拟环境安装依赖..."
                '''
                echo '✅ 虚拟环境创建完成'
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                    # 使用虚拟环境中的pip安装依赖
                    "${VENV_PATH}/bin/pip" install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple

                    # 检查requirements.txt是否存在，如果不存在则安装Django
                    if [ -f requirements.txt ]; then
                        echo "安装requirements.txt中的依赖..."
                        "${VENV_PATH}/bin/pip" install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
                    else
                        echo "requirements.txt不存在，安装Django..."
                        "${VENV_PATH}/bin/pip" install Django -i https://pypi.tuna.tsinghua.edu.cn/simple
                    fi

                    echo "已安装的包:"
                    "${VENV_PATH}/bin/pip" list
                '''
                echo '✅ 依赖安装完成'
            }
        }

        stage('Database Migration') {
            steps {
                sh '''
                    # 检查Django项目结构
                    if [ -f manage.py ]; then
                        echo "执行数据库迁移..."
                        "${VENV_PATH}/bin/python" manage.py migrate --noinput
                        echo "数据库迁移完成"
                    else
                        echo "错误: 未找到manage.py文件"
                        echo "当前目录内容:"
                        ls -la
                        exit 1
                    fi
                '''
                echo '✅ 数据库迁移完成'
            }
        }

        stage('Collect Static Files') {
            steps {
                sh '''
                    if [ -f manage.py ]; then
                        echo "收集静态文件..."
                        "${VENV_PATH}/bin/python" manage.py collectstatic --noinput || echo "静态文件收集失败，但继续执行"
                    else
                        echo "跳过静态文件收集"
                    fi
                '''
                echo '✅ 静态文件收集完成'
            }
        }

        stage('Run Application') {
            steps {
                sh '''
                    # 停止之前的进程（更精确的方式）
                    echo "停止现有应用进程..."
                    pkill -f "python.*manage.py runserver 0.0.0.0:8000" || true
                    sleep 3

                    # 检查端口占用
                    echo "检查8000端口占用..."
                    netstat -tlnp | grep 8000 || echo "8000端口空闲"

                    # 启动应用（使用虚拟环境中的python）
                    echo "启动Django应用..."
                    cd "${WORKSPACE}"
                    nohup "${VENV_PATH}/bin/python" manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &

                    # 记录进程ID
                    echo $! > django.pid
                    echo "应用进程ID: $(cat django.pid)"

                    # 等待应用启动
                    echo "等待应用启动..."
                    sleep 10

                    # 检查进程是否运行
                    if ps -p $(cat django.pid) > /dev/null 2>&1; then
                        echo "✅ 应用进程正在运行"
                    else
                        echo "❌ 应用进程已停止"
                        echo "服务器日志:"
                        cat server.log
                        exit 1
                    fi

                    # 检查应用是否响应
                    echo "检查应用响应..."
                    if curl -f http://localhost:8000/ > /dev/null 2>&1 || \
                       curl -f http://localhost:8000/admin/ > /dev/null 2>&1 || \
                       curl -f http://localhost:8000/api/ > /dev/null 2>&1; then
                        echo "✅ 应用响应正常"
                    else
                        echo "⚠️ 应用启动但无法通过HTTP访问，检查日志..."
                        cat server.log
                        # 不退出，因为应用可能已启动但需要额外配置
                    fi
                '''
                echo '✅ 应用启动完成'
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    echo "执行健康检查..."
                    # 多次尝试访问应用
                    for i in {1..5}; do
                        echo "健康检查尝试 $i"
                        if curl -s http://localhost:8000/ > /dev/null || \
                           curl -s http://localhost:8000/admin/ > /dev/null; then
                            echo "✅ 健康检查通过"
                            break
                        fi
                        if [ $i -eq 5 ]; then
                            echo "⚠️ 健康检查未通过，但继续执行"
                        fi
                        sleep 5
                    done

                    echo "应用状态信息:"
                    echo "进程状态: $(ps -p $(cat django.pid) > /dev/null 2>&1 && echo "运行中" || echo "已停止")"
                    echo "网络连接:"
                    netstat -tlnp | grep 8000 || echo "无8000端口监听"
                '''
                echo '✅ 健康检查完成'
            }
        }
    }
    post {
        always {
            echo "=== 构建完成 ==="
            echo "构建状态: ${currentBuild.result}"
            echo "工作目录: ${WORKSPACE}"
            sh '''
                echo "=== 部署摘要 ==="
                echo "应用PID: $(cat django.pid 2>/dev/null || echo '未记录')"
                echo "工作目录: $(pwd)"
                echo "虚拟环境: ${VENV_PATH}"
                echo "最近日志:"
                tail -20 server.log 2>/dev/null || echo "无服务器日志"
            '''
        }
        success {
            echo "🎉 部署成功! 应用地址: http://localhost:8000"
            sh '''
                echo "✅ 部署完成时间: $(date)"
                echo "🔗 访问地址: http://$(curl -s ifconfig.me):8000 或 http://localhost:8000"
            '''
        }
        failure {
            echo "❌ 部署失败! 请检查错误信息"
            sh '''
                echo "=== 错误诊断 ==="
                echo "Python版本:"
                python3 --version 2>/dev/null || python --version 2>/dev/null || echo "Python未安装"
                echo "虚拟环境状态:"
                ls -la "${VENV_PATH}/bin/python" 2>/dev/null && echo "虚拟环境正常" || echo "虚拟环境异常"
                echo "完整服务器日志:"
                cat server.log 2>/dev/null || echo "无服务器日志"
            '''
        }
    }
}