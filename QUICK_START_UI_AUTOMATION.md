# UI 自动化测试快速开始指南

## 5 分钟快速部署

### 步骤 1: 注册 URL 路由

编辑 `your_project/urls.py`：

```python
from django.urls import path, include

urlpatterns = [
    # ... 其他配置 ...
    path('', include('test_manager.urls.ui_urls')),
]
```

### 步骤 2: 运行数据库迁移

```bash
python manage.py migrate test_manager
```

### 步骤 3: 启动开发服务器

```bash
python manage.py runserver
```

### 步骤 4: 访问 UI 自动化测试

打开浏览器访问：
```
http://localhost:8000/ui-test-cases/
```

---

## 创建第一个 UI 测试

### 1. 创建测试用例

1. 点击左侧菜单 "UI自动化测试"
2. 点击 "创建UI测试用例" 按钮
3. 填写表单：
   - 名称：`登录功能测试`
   - URL：`https://example.com/login`
   - 浏览器：选择 `Chromium`
4. 点击 "创建测试用例"

### 2. 添加测试步骤

进入测试用例详情页面，点击 "添加步骤"：

**第 1 步**：导航到网站
- 操作：`navigate`
- 无需填写其他字段

**第 2 步**：输入用户名
- 操作：`fill`
- 定位方式：`CSS` 选择器
- 定位值：`input[name="username"]`
- 输入值：`test@example.com`

**第 3 步**：输入密码
- 操作：`fill`
- 定位方式：`CSS` 选择器
- 定位值：`input[name="password"]`
- 输入值：`password123`

**第 4 步**：点击登录按钮
- 操作：`click`
- 定位方式：`CSS` 选择器
- 定位值：`button[type="submit"]`

**第 5 步**：验证登录成功
- 操作：`assert_text`
- 定位方式：`CSS` 选择器
- 定位值：`.welcome-message`
- 输入值：`欢迎`（或期望的欢迎文本）

### 3. 运行测试

1. 在用例列表页点击 "运行" 按钮
2. 或进入用例详情页，点击 "运行测试" 按钮
3. 等待测试执行完成

### 4. 查看结果

1. 测试运行完成后会自动跳转到运行详情页
2. 查看执行结果：
   - 状态（通过/失败/错误）
   - 成功步骤数
   - 执行耗时
   - 每步执行结果

---

## 常用操作

### 如何定位元素？

**方法 1: 使用浏览器开发者工具**
1. 按 `F12` 打开开发者工具
2. 点击元素检查按钮 (左上角箭头)
3. 在网页上点击要定位的元素
4. 右键元素 → "Copy selector"
5. 粘贴到"定位值"字段

**方法 2: 手动编写选择器**

CSS 选择器示例：
```css
input[type="text"]              /* 所有文本输入框 */
button.btn-primary              /* class 为 btn-primary 的按钮 */
#submit                         /* id 为 submit 的元素 */
.form-group input[name="email"] /* 特定名称的输入框 */
```

XPath 示例：
```xpath
//input[@type='text']                    /* 所有文本输入框 */
//button[contains(text(), '登录')]       /* 包含"登录"文本的按钮 */
//div[@class='form-group']//input        /* form-group 内的输入框 */
```

### 等待元素加载

如果元素加载较慢，在点击/填充前添加等待步骤：

1. 新增步骤
2. 操作：`wait`
3. 输入值：`2`（等待 2 秒）

### 验证页面内容

使用验证操作检查页面状态：

- `assert_text` - 验证元素包含特定文本
- `assert_visible` - 验证元素可见
- `assert_url` - 验证当前 URL 包含特定内容

---

## 文件定位速查表

### 新增文件位置

```
项目根目录/
├── test_manager/
│   ├── views/
│   │   └── ui_views.py                    ← 新增视图
│   ├── urls/
│   │   └── ui_urls.py                     ← 新增 URL 配置
│   └── model/
│       └── ui_models.py                   ← 模型定义
│
└── templates/
    └── test_manager/
        ├── ui_test_case_list.html         ← 用例列表
        ├── ui_test_case_detail.html       ← 用例详情
        ├── ui_test_case_form.html         ← 用例表单
        ├── ui_test_case_confirm_delete.html
        ├── ui_test_step_form.html         ← 步骤表单
        ├── ui_test_run_list.html          ← 运行历史
        └── ui_test_run_detail.html        ← 运行详情
```

### 修改文件位置

```
templates/test_manager/partials/
└── nav_menu.html                         ← 添加菜单项
```

---

## URL 路由快速参考

```
GET  /ui-test-cases/                      # 用例列表
POST /ui-test-cases/create/               # 创建用例
GET  /ui-test-cases/<id>/                 # 用例详情
POST /ui-test-cases/<id>/edit/            # 编辑用例
POST /ui-test-cases/<id>/delete/          # 删除用例
POST /ui-test-cases/<id>/run/             # 运行用例

POST /ui-test-cases/<id>/steps/add/       # 添加步骤
POST /ui-test-steps/<id>/edit/            # 编辑步骤
POST /ui-test-steps/<id>/delete/          # 删除步骤

GET  /ui-test-runs/                       # 运行列表
GET  /ui-test-runs/<id>/                  # 运行详情
```

---

## 故障排除

### 访问页面 404

**问题**: 访问 `/ui-test-cases/` 显示 404

**解决方案**:
1. 确认已在 `urls.py` 中添加：`path('', include('test_manager.urls.ui_urls'))`
2. 重启 Django 开发服务器
3. 清除浏览器缓存（Ctrl+Shift+Del）

### 模型不存在

**问题**: 访问页面显示"no such table"错误

**解决方案**:
```bash
python manage.py migrate test_manager
```

### 菜单项不显示

**问题**: UI自动化测试菜单项未显示在导航栏

**解决方案**:
1. 检查 `nav_menu.html` 是否添加了菜单项
2. 清除浏览器缓存
3. 重新登录

### 测试无法运行

**问题**: 点击"运行测试"没有反应

**解决方案**:
1. 打开浏览器开发者工具（F12）→ Console 标签
2. 查看是否有 JavaScript 错误
3. 查看 Network 标签，确认请求是否发送
4. 检查服务器日志

---

## 性能优化提示

1. **使用 CSS 选择器** 优于 XPath
2. **最小化等待时间** - 避免硬等待
3. **分解大型测试** - 将长测试拆分为多个用例
4. **批量执行** - 使用测试运行计划

---

## 下一步学习

1. 阅读 `FRONTEND_IMPLEMENTATION_GUIDE.md` 了解详细功能
2. 查看 `UI_AUTOMATION_BEST_PRACTICES.md` 学习最佳实践
3. 浏览 `UI_AUTOMATION_ARCHITECTURE.md` 理解系统设计

---

## 常见问题速查

| 问题 | 答案 |
|------|------|
| 如何选择浏览器？ | 在创建用例时选择，支持 Chromium、Firefox、WebKit |
| 支持多少个步骤？ | 无限制，但建议单个用例不超过 20 步 |
| 如何调试失败的测试？ | 添加截图步骤，查看运行详情中的截图 |
| 支持并发执行吗？ | 目前不支持，可按顺序执行多个用例 |
| 如何导出测试结果？ | 在运行详情页面可复制相关信息，后续支持导出 |

---

## 快速命令参考

```bash
# 运行迁移
python manage.py migrate test_manager

# 创建超级用户（如需）
python manage.py createsuperuser

# 启动开发服务器
python manage.py runserver

# 收集静态文件（生产环境）
python manage.py collectstatic --noinput

# 查看所有 URL
python manage.py show_urls
```

---

## 获取帮助

- 📖 文档：查看 `FRONTEND_IMPLEMENTATION_GUIDE.md`
- 🐛 调试：检查浏览器开发者工具和服务器日志
- 💬 反馈：在 GitHub Issues 中报告问题
- 📧 联系：联系技术支持团队

---

**祝您使用愉快！** 🎉

如有任何问题，请参考完整的 `FRONTEND_IMPLEMENTATION_GUIDE.md` 文档。
