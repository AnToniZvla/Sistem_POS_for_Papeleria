-- =====================================================================================
-- SCRIPT DE ESQUEMA 3NF Y MIGRACIÓN AUTOMÁTICA SIN PÉRDIDA DE DATOS
-- Motor: MySQL / MariaDB (Compatible con XAMPP / phpMyAdmin)
-- Base de datos objetivo: `database`
-- =====================================================================================

CREATE DATABASE IF NOT EXISTS `database`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `database`;

SET FOREIGN_KEY_CHECKS = 0;

-- 1. TABLA: roles (3NF)
CREATE TABLE IF NOT EXISTS `roles` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(30) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `roles` (`id`, `nombre`) VALUES
(1, 'Admin'),
(2, 'Cajero');

-- 2. TABLA: usuarios (3NF)
CREATE TABLE IF NOT EXISTS `usuarios` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `nombre_completo` VARCHAR(100) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `rol_id` INT NOT NULL,
    `activo` TINYINT(1) NOT NULL DEFAULT 1,
    `creado_en` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_usuarios_rol` FOREIGN KEY (`rol_id`) REFERENCES `roles` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. TABLA: categorias (3NF)
CREATE TABLE IF NOT EXISTS `categorias` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `nombre` VARCHAR(60) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT IGNORE INTO `categorias` (`id`, `nombre`) VALUES
(1, 'General'),
(2, 'Cuadernos y Papel'),
(3, 'Escritura'),
(4, 'Arte y Manualidades'),
(5, 'Oficina');

-- 4. CREACIÓN DE TABLAS BASE SI LA BD ESTÁ COMPLETAMENTE VACÍA
CREATE TABLE IF NOT EXISTS `productos` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `codigo_barras` VARCHAR(64) NULL UNIQUE,
    `nombre` VARCHAR(100) NOT NULL UNIQUE,
    `categoria_id` INT NOT NULL DEFAULT 1,
    `precio_costo` DECIMAL(10,2) NOT NULL,
    `precio_venta` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    `stock` INT NOT NULL DEFAULT 0,
    `stock_minimo` INT NOT NULL DEFAULT 5,
    `activo` TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT `fk_productos_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `ventas` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `usuario_id` INT NULL,
    `fecha` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `total_venta` DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    CONSTRAINT `fk_ventas_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS `detalles_ventas` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `venta_id` INT NOT NULL,
    `producto_id` INT NOT NULL,
    `cantidad` INT NOT NULL,
    `precio_costo_historico` DECIMAL(10,2) NOT NULL,
    `precio_venta_unitario` DECIMAL(10,2) NOT NULL,
    CONSTRAINT `fk_detalles_venta` FOREIGN KEY (`venta_id`) REFERENCES `ventas` (`id`)
        ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT `fk_detalles_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. TABLA: movimientos_inventario (Kardex de Auditoría en 3NF)
CREATE TABLE IF NOT EXISTS `movimientos_inventario` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `producto_id` INT NOT NULL,
    `usuario_id` INT NULL,
    `tipo` ENUM('ENTRADA', 'SALIDA_VENTA', 'AJUSTE') NOT NULL,
    `cantidad` INT NOT NULL,
    `motivo` VARCHAR(150) NOT NULL,
    `fecha` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_movimientos_producto` FOREIGN KEY (`producto_id`) REFERENCES `productos` (`id`)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT `fk_movimientos_usuario` FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
        ON UPDATE CASCADE ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================================================
-- 6. PROCEDIMIENTO DE MIGRACIÓN AUTOMÁTICA DESDE EL ESQUEMA ANTIGUO
-- Transforma las tablas existentes sin perder productos ni historial de ventas
-- =====================================================================================
DROP PROCEDURE IF EXISTS `migrar_esquema_3nf`;

DELIMITER $$

CREATE PROCEDURE `migrar_esquema_3nf`()
BEGIN
    DECLARE v_db VARCHAR(64);
    SET v_db = DATABASE();

    -- -------------------------------------------------------------------------
    -- A. MIGRACIÓN DE TABLA `productos`
    -- -------------------------------------------------------------------------
    -- 1. Si existe la columna antigua `cantidad` (decimal o int), renombrarla a `stock` (INT)
    IF EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'cantidad'
    ) THEN
        UPDATE `productos` SET `cantidad` = ROUND(`cantidad`);
        ALTER TABLE `productos` CHANGE COLUMN `cantidad` `stock` INT NOT NULL DEFAULT 0;
    END IF;

    -- 2. Agregar `codigo_barras` si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'codigo_barras'
    ) THEN
        ALTER TABLE `productos` ADD COLUMN `codigo_barras` VARCHAR(64) NULL UNIQUE AFTER `id`;
    END IF;

    -- 3. Agregar `categoria_id` con valor por defecto 1 ('General')
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'categoria_id'
    ) THEN
        ALTER TABLE `productos` ADD COLUMN `categoria_id` INT NOT NULL DEFAULT 1 AFTER `nombre`;
    END IF;

    -- 4. Agregar `precio_venta` si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'precio_venta'
    ) THEN
        ALTER TABLE `productos` ADD COLUMN `precio_venta` DECIMAL(10,2) NOT NULL DEFAULT 0.00 AFTER `precio_costo`;
    END IF;

    -- 5. Agregar `stock_minimo` si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'stock_minimo'
    ) THEN
        ALTER TABLE `productos` ADD COLUMN `stock_minimo` INT NOT NULL DEFAULT 5 AFTER `stock`;
    END IF;

    -- 6. Agregar `activo` si no existe
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'activo'
    ) THEN
        ALTER TABLE `productos` ADD COLUMN `activo` TINYINT(1) NOT NULL DEFAULT 1 AFTER `stock_minimo`;
    END IF;

    -- 7. Normalizar nombres duplicados antes de colocar índice UNIQUE en `productos.nombre`
    UPDATE `productos` p1
    INNER JOIN `productos` p2
        ON p1.nombre = p2.nombre AND p1.id > p2.id
    SET p1.nombre = CONCAT(p1.nombre, ' (#', p1.id, ')');

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'nombre' AND NON_UNIQUE = 0
    ) THEN
        ALTER TABLE `productos` ADD UNIQUE INDEX `uk_productos_nombre` (`nombre`);
    END IF;

    -- 8. Asegurar llave foránea `fk_productos_categoria`
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'productos' AND CONSTRAINT_NAME = 'fk_productos_categoria'
    ) THEN
        ALTER TABLE `productos`
            ADD CONSTRAINT `fk_productos_categoria`
            FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id`)
            ON UPDATE CASCADE ON DELETE RESTRICT;
    END IF;

    -- -------------------------------------------------------------------------
    -- B. MIGRACIÓN DE TABLA `ventas`
    -- -------------------------------------------------------------------------
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'ventas' AND COLUMN_NAME = 'usuario_id'
    ) THEN
        ALTER TABLE `ventas` ADD COLUMN `usuario_id` INT NULL AFTER `id`;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.TABLE_CONSTRAINTS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'ventas' AND CONSTRAINT_NAME = 'fk_ventas_usuario'
    ) THEN
        ALTER TABLE `ventas`
            ADD CONSTRAINT `fk_ventas_usuario`
            FOREIGN KEY (`usuario_id`) REFERENCES `usuarios` (`id`)
            ON UPDATE CASCADE ON DELETE SET NULL;
    END IF;

    -- -------------------------------------------------------------------------
    -- C. MIGRACIÓN DE TABLA `detalles_ventas` (3NF)
    -- -------------------------------------------------------------------------
    -- 1. Asegurar que `cantidad` sea INT
    UPDATE `detalles_ventas` SET `cantidad` = ROUND(`cantidad`);
    ALTER TABLE `detalles_ventas` MODIFY COLUMN `cantidad` INT NOT NULL;

    -- 2. Renombrar `precio_costo` -> `precio_costo_historico`
    IF EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'detalles_ventas' AND COLUMN_NAME = 'precio_costo'
    ) THEN
        ALTER TABLE `detalles_ventas`
            CHANGE COLUMN `precio_costo` `precio_costo_historico` DECIMAL(10,2) NOT NULL;
    END IF;

    -- 3. Renombrar `precio_venta` -> `precio_venta_unitario`
    IF EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'detalles_ventas' AND COLUMN_NAME = 'precio_venta'
    ) THEN
        ALTER TABLE `detalles_ventas`
            CHANGE COLUMN `precio_venta` `precio_venta_unitario` DECIMAL(10,2) NOT NULL;
    END IF;

    -- 4. Eliminar columna redundante `precio_venta_total` para cumplir 3NF
    IF EXISTS (
        SELECT 1 FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = v_db AND TABLE_NAME = 'detalles_ventas' AND COLUMN_NAME = 'precio_venta_total'
    ) THEN
        ALTER TABLE `detalles_ventas` DROP COLUMN `precio_venta_total`;
    END IF;

    -- -------------------------------------------------------------------------
    -- D. POBLAR `precio_venta` EN PRODUCTOS MIGRADOS QUE TENGAN 0.00
    -- Usa el último precio vendido en `detalles_ventas` o aplica +30% sobre costo
    -- -------------------------------------------------------------------------
    UPDATE `productos` p
    LEFT JOIN (
        SELECT dv1.producto_id, MAX(dv1.precio_venta_unitario) AS ultimo_precio
        FROM `detalles_ventas` dv1
        GROUP BY dv1.producto_id
    ) hist ON p.id = hist.producto_id
    SET p.precio_venta = COALESCE(hist.ultimo_precio, ROUND(p.precio_costo * 1.30, 2))
    WHERE p.precio_venta <= 0;

    -- -------------------------------------------------------------------------
    -- E. REGISTRAR MOVIMIENTO INICIAL DE INVENTARIO PARA PRODUCTOS MIGRADOS
    -- -------------------------------------------------------------------------
    INSERT INTO `movimientos_inventario` (`producto_id`, `usuario_id`, `tipo`, `cantidad`, `motivo`)
    SELECT p.id, NULL, 'ENTRADA', p.stock, 'Inventario inicial migrado a esquema 3NF'
    FROM `productos` p
    WHERE p.stock > 0
      AND NOT EXISTS (
          SELECT 1 FROM `movimientos_inventario` m WHERE m.producto_id = p.id
      );

END$$

DELIMITER ;

CALL `migrar_esquema_3nf`();
DROP PROCEDURE IF EXISTS `migrar_esquema_3nf`;

SET FOREIGN_KEY_CHECKS = 1;
