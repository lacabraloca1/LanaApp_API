-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Versión del servidor:         8.4.3 - MySQL Community Server - GPL
-- SO del servidor:              Win64
-- HeidiSQL Versión:             12.8.0.6908
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;


-- Volcando estructura de base de datos para lana_app
DROP DATABASE IF EXISTS `lana_app`;
CREATE DATABASE IF NOT EXISTS `lana_app` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `lana_app`;

-- Volcando estructura para tabla lana_app.categorias
DROP TABLE IF EXISTS `categorias`;
CREATE TABLE IF NOT EXISTS `categorias` (
  `id_categoria` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(50) NOT NULL,
  `tipo` enum('ingreso','egreso','otro') NOT NULL,
  PRIMARY KEY (`id_categoria`),
  UNIQUE KEY `uq_categorias_nombre` (`nombre`),
  KEY `idx_categorias_tipo` (`tipo`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla lana_app.pagos
DROP TABLE IF EXISTS `pagos`;
CREATE TABLE IF NOT EXISTS `pagos` (
  `id_pago` int NOT NULL AUTO_INCREMENT,
  `id_usuario` int NOT NULL,
  `descripcion` varchar(255) NOT NULL,
  `monto` decimal(10,2) NOT NULL,
  `fecha_programada` datetime NOT NULL,
  `categoria_id` int DEFAULT NULL,
  `periodicidad` enum('none','weekly','monthly') NOT NULL DEFAULT 'none',
  `proxima_ejecucion` date NOT NULL,
  `activo` tinyint(1) NOT NULL DEFAULT '1',
  PRIMARY KEY (`id_pago`),
  KEY `fk_pago_categoria` (`categoria_id`),
  KEY `idx_pago_usuario` (`id_usuario`),
  KEY `idx_pago_proxima` (`proxima_ejecucion`),
  KEY `idx_pago_activo` (`activo`),
  CONSTRAINT `fk_pago_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id_categoria`) ON DELETE SET NULL,
  CONSTRAINT `fk_pago_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla lana_app.presupuestos
DROP TABLE IF EXISTS `presupuestos`;
CREATE TABLE IF NOT EXISTS `presupuestos` (
  `id_presupuesto` int NOT NULL AUTO_INCREMENT,
  `id_usuario` int NOT NULL,
  `id_categoria` int NOT NULL,
  `monto_mensual` decimal(10,2) NOT NULL,
  `mes` tinyint NOT NULL,
  `año` smallint NOT NULL,
  PRIMARY KEY (`id_presupuesto`),
  UNIQUE KEY `uq_pres_usuario_categoria_mes_anio` (`id_usuario`,`id_categoria`,`mes`,`año`),
  KEY `fk_pres_categoria` (`id_categoria`),
  KEY `idx_pres_mes_anio` (`mes`,`año`),
  CONSTRAINT `fk_pres_categoria` FOREIGN KEY (`id_categoria`) REFERENCES `categorias` (`id_categoria`) ON DELETE CASCADE,
  CONSTRAINT `fk_pres_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla lana_app.transacciones
DROP TABLE IF EXISTS `transacciones`;
CREATE TABLE IF NOT EXISTS `transacciones` (
  `id_transaccion` int NOT NULL AUTO_INCREMENT,
  `id_usuario` int NOT NULL,
  `tipo` enum('ingreso','egreso','envio','solicitud') NOT NULL,
  `monto` decimal(10,2) NOT NULL,
  `fecha` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `descripcion` varchar(255) DEFAULT NULL,
  `categoria_id` int DEFAULT NULL,
  `destinatario_id` int DEFAULT NULL,
  `estado` enum('pendiente','completada','cancelada') NOT NULL DEFAULT 'completada',
  `frecuencia` varchar(50) DEFAULT NULL,
  `fecha_fin` date DEFAULT NULL,
  PRIMARY KEY (`id_transaccion`),
  KEY `fk_tx_destinatario` (`destinatario_id`),
  KEY `idx_tx_usuario_fecha` (`id_usuario`,`fecha`),
  KEY `idx_tx_tipo` (`tipo`),
  KEY `idx_tx_categoria` (`categoria_id`),
  CONSTRAINT `fk_tx_categoria` FOREIGN KEY (`categoria_id`) REFERENCES `categorias` (`id_categoria`) ON DELETE SET NULL,
  CONSTRAINT `fk_tx_destinatario` FOREIGN KEY (`destinatario_id`) REFERENCES `usuarios` (`id_usuario`) ON DELETE SET NULL,
  CONSTRAINT `fk_tx_usuario` FOREIGN KEY (`id_usuario`) REFERENCES `usuarios` (`id_usuario`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para tabla lana_app.usuarios
DROP TABLE IF EXISTS `usuarios`;
CREATE TABLE IF NOT EXISTS `usuarios` (
  `id_usuario` int NOT NULL AUTO_INCREMENT,
  `nombre` varchar(120) NOT NULL,
  `correo` varchar(190) NOT NULL,
  `telefono` varchar(30) NOT NULL,
  `contrasena_hash` varchar(255) NOT NULL,
  `pin_seguridad` varchar(255) DEFAULT NULL,
  `saldo` decimal(10,2) NOT NULL DEFAULT '0.00',
  `fecha_registro` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `creado_en` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id_usuario`),
  UNIQUE KEY `uq_usuarios_correo` (`correo`),
  UNIQUE KEY `uq_usuarios_telefono` (`telefono`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- La exportación de datos fue deseleccionada.

-- Volcando estructura para disparador lana_app.trg_pagos_set_proxima_ejecucion
DROP TRIGGER IF EXISTS `trg_pagos_set_proxima_ejecucion`;
SET @OLDTMP_SQL_MODE=@@SQL_MODE, SQL_MODE='ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
DELIMITER //
CREATE TRIGGER `trg_pagos_set_proxima_ejecucion` BEFORE INSERT ON `pagos` FOR EACH ROW BEGIN
  IF NEW.proxima_ejecucion IS NULL THEN
    SET NEW.proxima_ejecucion = DATE(NEW.fecha_programada);
  END IF;
END//
DELIMITER ;
SET SQL_MODE=@OLDTMP_SQL_MODE;

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
