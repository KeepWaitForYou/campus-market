-- ============================================================
-- 校园二手交易平台 - MySQL 初始化脚本
-- 仅初始化数据库与字符集；业务表由 Django migrations 创建
-- ============================================================

-- 确保数据库存在（与 mysql 镜像 MYSQL_DATABASE 一致）
CREATE DATABASE IF NOT EXISTS `campus_market`
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE `campus_market`;

-- 默认商品分类在 manage.py create_default_admin 命令中同步创建，
-- 避免与 Django ORM 迁移顺序冲突。