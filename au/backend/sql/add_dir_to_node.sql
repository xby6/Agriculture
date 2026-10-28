-- 为node_info表添加dir字段
ALTER TABLE node_info ADD COLUMN dir INT NULL COMMENT '关联文件夹ID';

-- 可选：为dir字段添加索引以提高查询性能
-- CREATE INDEX idx_node_info_dir ON node_info(dir);
