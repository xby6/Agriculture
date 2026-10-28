、-- 水稻病害智能监测与预测平台：界面菜单迁移脚本
-- 适用于已经初始化过 sys_menu / sys_dept 的 PostgreSQL 数据库。
BEGIN;

-- 1. 原有技术业务入口改为隐藏，避免与新版“农业业务中心”重复。
UPDATE sys_menu SET visible = '1' WHERE menu_id IN (4, 5, 6);

-- 2. 平台管理与运维菜单农业化命名。
UPDATE sys_menu SET menu_name = '平台权限管理', remark = '农业平台权限管理目录' WHERE menu_id = 1;
UPDATE sys_menu SET menu_name = '平台运行维护', remark = '农业平台运行维护目录' WHERE menu_id = 2;
UPDATE sys_menu SET menu_name = '系统开发工具', visible = '1' WHERE menu_id = 3;
UPDATE sys_menu SET menu_name = '农业数据中心' WHERE menu_id = 4;
UPDATE sys_menu SET menu_name = '农业模型服务' WHERE menu_id = 5;
UPDATE sys_menu SET menu_name = '模型分析任务' WHERE menu_id = 6;

UPDATE sys_menu SET menu_name = '平台用户' WHERE menu_id = 100;
UPDATE sys_menu SET menu_name = '角色权限' WHERE menu_id = 101;
UPDATE sys_menu SET menu_name = '功能菜单' WHERE menu_id = 102;
UPDATE sys_menu SET menu_name = '基地组织' WHERE menu_id = 103;
UPDATE sys_menu SET menu_name = '农业岗位' WHERE menu_id = 104;
UPDATE sys_menu SET menu_name = '农情公告' WHERE menu_id = 107;
UPDATE sys_menu SET menu_name = '服务运行监控' WHERE menu_id = 112;
UPDATE sys_menu SET menu_name = '数据缓存监控' WHERE menu_id = 113;
UPDATE sys_menu SET menu_name = '缓存数据列表' WHERE menu_id = 114;

-- 3. 组织机构示例数据农业化。
UPDATE sys_dept SET dept_name = '水稻病害研究中心' WHERE dept_id = 100;
UPDATE sys_dept SET dept_name = '海城试验基地', leader = '基地负责人' WHERE dept_id = 101;

COMMIT;
