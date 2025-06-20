

# EasyTesting

EasyTesting 是一个功能强大的测试管理平台，提供全面的测试功能，包括测试用例、测试套件、测试运行和测试报告等。它支持用户友好的界面，便于管理和执行测试任务，适用于Web应用的自动化测试。

## 功能特点

- **测试用例管理**：创建、编辑、运行和删除测试用例。
- **测试套件管理**：组织测试用例为测试套件，并支持套件运行。
- **测试运行**：支持手动和定时测试运行，提供实时测试结果。
- **测试报告**：测试运行后生成详细的测试报告，支持查看和导出。
- **Mock数据生成**：提供Mock数据支持，便于测试接口开发。
- **定时任务**：支持定时执行测试套件，可配置邮件通知。
- **邮件配置**：提供邮件配置功能，支持测试结果的通知发送。
- **用户管理**：包括注册、登录、个人资料管理和修改密码等功能。

## 安装指南

1. 克隆项目到本地：

   ```bash
   git clone <repository-url>
   ```

2. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

3. 创建数据库并迁移：

   ```bash
   python manage.py migrate
   ```

4. 启动服务器：

   ```bash
   python manage.py runserver
   ```

5. (可选) 启动 Celery worker：

   ```bash
   celery -A EasyTesting worker --loglevel=info
   ```

   启动 Celery beat：

   ```bash
   celery -A EasyTesting beat --loglevel=info
   ```

## 使用说明

### 用户注册与登录

- **注册**：访问 `/register/` 创建新账户。
- **登录**：访问 `/login/` 进行登录。

### 项目管理

- **创建项目**：登录后访问 `/project/new/` 创建新项目。
- **编辑项目**：通过 `/project/<id>/edit/` 编辑已有项目。
- **删除项目**：通过 `/project/<id>/delete/` 删除项目。

### 环境配置

- **添加环境**：在项目详情页 `/project/<id>/` 中点击 "Add Environment"。
- **编辑环境**：访问 `/environment/<id>/edit/` 编辑环境变量。
- **删除环境**：访问 `/environment/<id>/delete/` 删除环境。

### 测试用例管理

- **创建测试用例**：在项目详情页 `/project/<id>/` 中点击 "Add Test Case"。
- **编辑测试用例**：访问 `/testcase/<id>/edit/`。
- **运行测试用例**：访问 `/testcase/<id>/run/` 并选择环境执行测试。
- **删除测试用例**：访问 `/testcase/<id>/delete/`。

### 测试套件管理

- **创建测试套件**：在项目详情页 `/project/<id>/` 中点击 "Add Test Suite"。
- **编辑测试套件**：访问 `/testsuite/<id>/edit/`。
- **运行测试套件**：访问 `/testsuite/<id>/run/` 并选择环境执行测试。
- **删除测试套件**：访问 `/testsuite/<id>/delete/`。

### 测试运行与报告

- **查看测试运行**：访问 `/testrun/<id>/` 获取测试执行详情。
- **生成测试报告**：测试运行完成后，可通过 `/testreport/<id>/` 查看报告。
- **导出报告**：支持导出测试报告为HTML、PDF等格式。

### Mock 数据生成

- **生成Mock数据**：访问 `/mockdata/` 创建Mock数据，支持数据导出和删除。

### 定时任务

- **添加定时任务**：访问 `/scheduledtask/new/` 配置定时执行测试套件。
- **编辑定时任务**：访问 `/scheduledtask/<id>/edit/`。
- **手动执行定时任务**：通过 `/scheduledtask/<id>/run/` 立立即执行。
- **查看定时任务日志**：访问 `/tasklog/<id>/` 查看执行日志。

### 邮件通知配置

- **配置邮件**：管理员访问 `/emailconfig/<id>/` 配置邮件服务器设置。
- **测试邮件连接**：在邮件配置页点击 "Test Connection" 按钮。
- **激活邮件配置**：点击 `/emailconfig/<id>/activate/` 设为当前激活配置。

## API 文档

EasyTesting 提供 RESTful API，使用 Django REST framework 实现。

### 项目 API

- `GET /api/project/`：获取项目列表。
- `POST /api/project/`：创建新项目。
- `GET /api/project/<id>/`：获取指定项目详情。
- `PUT /api/project/<id>/`：更新项目。
- `DELETE /api/project/<id>/`：删除项目。

### 测试用例 API

- `GET /api/testcase/`：获取测试用例列表。
- `POST /api/testcase/`：创建新测试用例。
- `GET /api/testcase/<id>/`：获取测试用例详情。
- `POST /api/testcase/<id>/run/`：运行测试用例。
- `PUT /api/testcase/<id>/`：更新测试用例。
- `DELETE /api/testcase/<id>/`：删除测试用例。

### 测试套件 API

- `GET /api/testsuite/`：获取测试套件列表。
- `POST /api/testsuite/`：创建新测试套件。
- `GET /api/testsuite/<id>/`：获取测试套件详情。
- `POST /api/testsuite/<id>/run/`：运行测试套件。
- `PUT /api/testsuite/<id>/`：更新测试套件。
- `DELETE /api/testsuite/<id>/`：删除测试套件。

### 测试运行 API

- `GET /api/testrun/`：获取测试运行列表。
- `GET /api/testrun/<id>/results/`：获取测试运行结果。

### 测试报告 API

- `GET /api/testreport/`：获取测试报告列表。
- `GET /api/testreport/<id>/`：获取报告详情。
- `POST /api/testreport/<id>/delete/`：删除报告。

### Mock数据 API

- `GET /api/mockdata/`：获取Mock数据列表。
- `POST /api/mockdata/`：创建Mock数据。
- `GET /api/mockdata/<id>/`：获取指定Mock数据详情。
- `PUT /api/mockdata/<id>/`：更新Mock数据。
- `DELETE /api/mockdata/<id>/`：删除Mock数据。

## License

本项目采用 [MIT License](LICENSE)。

## 致谢

感谢所有为本项目做出贡献的伙伴。