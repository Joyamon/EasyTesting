# EasyTesting

使用Django、Django REST框架、SQLite、Bootstrap和HTTPRunner构建的综合测试平台。

## 推荐版本
- python3.9 
- Django==4.2.11 
- djangorestframework==3.15.2
- httprunner==4.3.0

## 功能特点

- 创建和管理测试项目
- 使用变量定义测试环境
- 使用请求详细信息和验证规则创建API测试用例
- 将测试用例组织到测试套件中
- 执行测试并查看结果
- 用于与其他工具集成的RESTful API

## 快速开始

1. Clone the repository
2. Create a virtual environment:
   \`\`\`
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   \`\`\`
3. Install dependencies:
   \`\`\`
   pip install -r requirements.txt
   \`\`\`
4. Run migrations:
   \`\`\`
   python manage.py migrate
   \`\`\`
5. Create a superuser:
   \`\`\`
   python manage.py createsuperuser
   \`\`\`
6. Run the development server:
   \`\`\`
   python manage.py runserver
   \`\`\`

## 使用

1. Access the admin interface at http://localhost:8000/admin/
2. Log in with your superuser credentials
3. Create projects, environments, test cases, and test suites
4. Execute tests and view results

## 效果截图

### 注册
<img src="static/pic/注册.png" />

### 登录
<img src="static/pic/登录.png" />

### 面板
<img src="static/pic/Dashboard.png" />

### 项目
<img src="static/pic/project.png" />

### 项目详情
<img src="static/pic/projectDetails.png" />

### 环境
<img src="static/pic/Environments.png" />

### 测试用例
<img src="static/pic/Test Cases .png" />

### 测试用例详情
<img src="static/pic/caseDetail.png" />

### 测试套件
<img src="static/pic/Test Suites .png" />

### 测试套件详情
<img src="static/pic/suiteDetail.png" />

### 测试运行
<img src="static/pic/Test Runs .png" />

### 测试结果
<img src="static/pic/testresultsDetail.png" />

### 测试用例分组
<img src="static/pic/All Test Case Groups .png" />

### 测试套件分组
<img src="static/pic/All Test Suite Groups  .png" />

### 个人资料
<img src="static/pic/个人资料.png" />

### 修改密码
<img src="static/pic/修改密码.png" />

### 邮件配置列表
<img src="static/pic/邮件配置列表.png" />

## License
This project is licensed under the MIT License.

