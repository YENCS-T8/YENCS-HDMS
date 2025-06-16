-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:9901
-- Generation Time: Jun 16, 2025 at 07:49 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.0.30

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `hospital`
--

-- --------------------------------------------------------

--
-- Table structure for table `activity_log`
--

CREATE TABLE `activity_log` (
  `id` int(11) NOT NULL,
  `message` varchar(200) NOT NULL,
  `timestamp` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `activity_log`
--

INSERT INTO `activity_log` (`id`, `message`, `timestamp`) VALUES
(1, 'Added 2 units to blood type 1.', '2025-06-14 11:53:48'),
(2, 'New medicine \'Sample\' added to inventory with stock 20.', '2025-06-14 12:04:22'),
(3, 'Added 30 units to drug ID: 8.', '2025-06-14 12:04:35'),
(4, 'Generated drug order for 4 low-stock items.', '2025-06-14 12:06:31'),
(5, 'Generated drug order for 4 low-stock items.', '2025-06-14 12:07:07'),
(6, 'Generated drug order for 4 low-stock items.', '2025-06-14 12:07:18'),
(7, 'Sent low stock alert for 4 drug(s).', '2025-06-14 12:07:25'),
(8, 'Generated drug order for 4 low-stock items.', '2025-06-14 12:07:50'),
(9, 'Sent low stock alert for 4 drug(s).', '2025-06-14 12:08:04'),
(10, 'Sent critical blood stock alert for 1 type(s).', '2025-06-14 12:09:08'),
(11, 'Generated drug order for 4 low-stock items.', '2025-06-14 12:16:01'),
(12, 'Restocked 2 out of stock drug(s).', '2025-06-14 12:16:11'),
(13, 'Issued 2 units of Sample (ID: 8).', '2025-06-14 12:19:11'),
(14, 'New medicine \'Paracetom\' added to inventory with stock 100.', '2025-06-14 12:36:34'),
(15, 'Sent critical blood stock alert for 1 type(s).', '2025-06-14 12:43:13'),
(16, 'Sent low stock alert for 2 drug(s).', '2025-06-14 12:44:27'),
(17, 'Generated drug order for 2 low-stock items.', '2025-06-14 12:46:48'),
(18, 'Generated drug order for 2 low-stock items.', '2025-06-14 12:48:55'),
(19, 'Sent low stock alert for 2 drug(s).', '2025-06-14 12:49:02'),
(20, 'Issued 1 units of Sample (ID: 8).', '2025-06-14 12:49:37'),
(21, 'Broadcasted Emergency Alert: \'blue\'', '2025-06-14 16:14:08'),
(22, 'Toggled Screen 1 to OFFLINE', '2025-06-14 16:14:39'),
(23, 'Broadcasted Emergency Alert: \'red\'', '2025-06-14 16:22:44'),
(24, 'Cleared content on all displays', '2025-06-14 16:22:57'),
(25, 'Broadcasted to all displays: \'HI\'', '2025-06-14 16:26:53'),
(26, 'Sent Token 2 to Screen 1', '2025-06-14 16:27:42'),
(27, 'Cleared content on Screen 2', '2025-06-14 16:27:55'),
(28, 'Broadcasted Emergency Alert: \'blue\'', '2025-06-14 16:31:41'),
(29, 'Cleared content on Screen 2', '2025-06-14 16:31:52'),
(30, 'Sent Token 4 to Screen 2', '2025-06-14 16:32:48'),
(31, 'Display 1 connected from IP: 127.0.0.1', '2025-06-14 16:35:16'),
(32, 'Display 2 connected from IP: 127.0.0.1', '2025-06-14 16:35:16'),
(33, 'Display 3 connected from IP: 127.0.0.1', '2025-06-14 16:35:17'),
(34, 'Sent Token 4 to Screen 2', '2025-06-14 16:35:24'),
(35, 'Cleared content on all displays', '2025-06-14 16:35:40'),
(36, 'Display 3 connected/reconnected from IP: 127.0.0.1', '2025-06-14 16:38:33'),
(37, 'Display 1 connected/reconnected from IP: 127.0.0.1', '2025-06-14 16:44:23'),
(38, 'Display 1 connected/reconnected from IP: 127.0.0.1', '2025-06-14 16:44:27'),
(39, 'Display 1 connected/reconnected from IP: 127.0.0.1', '2025-06-14 16:46:36'),
(40, 'Display 1 connected/reconnected from IP: 127.0.0.1', '2025-06-14 16:47:41'),
(41, 'Display 1 connected/reconnected from IP: 127.0.0.1', '2025-06-14 16:51:33'),
(42, 'Display 1 connected/reconnected from IP: 127.0.0.1', '2025-06-14 16:53:19'),
(43, 'Manually set Screen 1 to OFFLINE (via direct link)', '2025-06-14 16:53:39'),
(44, 'Display 1 connected/reconnected from IP: 127.0.0.1', '2025-06-14 16:53:44'),
(45, 'Display 1 connected/reconnected from IP: 127.0.0.1', '2025-06-14 16:59:08'),
(46, 'Display 1 connected/reconnected from IP: 127.0.0.1', '2025-06-14 16:59:40'),
(47, 'Sent low stock alert for 2 drug(s).', '2025-06-15 17:31:04');

-- --------------------------------------------------------

--
-- Table structure for table `blood_bank`
--

CREATE TABLE `blood_bank` (
  `blood_id` int(11) NOT NULL,
  `type` varchar(5) NOT NULL,
  `units` int(11) DEFAULT 0,
  `critical_level` int(11) DEFAULT 5
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `blood_bank`
--

INSERT INTO `blood_bank` (`blood_id`, `type`, `units`, `critical_level`) VALUES
(1, 'A+', 5, 5),
(2, 'A-', 3, 3),
(3, 'B+', 6, 5),
(4, 'B-', 2, 2),
(5, 'AB+', 5, 5),
(6, 'AB-', 4, 4),
(7, 'O+', 9, 6),
(8, 'O-', 3, 3);

-- --------------------------------------------------------

--
-- Table structure for table `broadcast_message`
--

CREATE TABLE `broadcast_message` (
  `id` int(11) NOT NULL,
  `message` varchar(200) NOT NULL,
  `timestamp` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `code_definitions`
--

CREATE TABLE `code_definitions` (
  `id` int(11) NOT NULL,
  `code_name` varchar(50) NOT NULL,
  `description` varchar(100) DEFAULT NULL,
  `color` varchar(20) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `code_definitions`
--

INSERT INTO `code_definitions` (`id`, `code_name`, `description`, `color`) VALUES
(1, 'Code Blue', 'Medical Emergency', '#3498db'),
(2, 'Code Red', 'Fire Emergency', '#e74c3c'),
(3, 'Code Green', 'Evacuation', '#2ecc71'),
(4, 'Code Yellow', 'Disaster / Mass Casualty', '#f1c40f'),
(5, 'Code Orange', 'Hazardous Material Spill', '#e67e22'),
(6, 'Code Black', 'Bomb Threat', '#000000'),
(7, 'Code White', 'Evacuation of Pediatrics', '#ffffff'),
(8, 'Code Brown', 'Severe Weather Alert', '#8e44ad'),
(9, 'Code Silver', 'Active Shooter', '#7f8c8d'),
(10, 'Code Pink', 'Infant Abduction', '#ff69b4');

-- --------------------------------------------------------

--
-- Table structure for table `consultation_schedule`
--

CREATE TABLE `consultation_schedule` (
  `id` int(11) NOT NULL,
  `doctor_name` varchar(100) DEFAULT NULL,
  `specialization` varchar(100) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `start_time` time DEFAULT NULL,
  `end_time` time DEFAULT NULL,
  `room_no` varchar(10) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `consultation_tokens`
--

CREATE TABLE `consultation_tokens` (
  `token_id` int(11) NOT NULL,
  `consultation_id` int(11) DEFAULT NULL,
  `patient_name` varchar(255) DEFAULT NULL,
  `token_number` int(11) DEFAULT NULL,
  `status` enum('Waiting','In Progress','Completed') DEFAULT 'Waiting'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `departments`
--

CREATE TABLE `departments` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `departments`
--

INSERT INTO `departments` (`id`, `name`) VALUES
(1, 'Cardiology'),
(2, 'Orthopedics'),
(3, 'Neurology'),
(4, 'Pediatrics');

-- --------------------------------------------------------

--
-- Table structure for table `display_screen`
--

CREATE TABLE `display_screen` (
  `id` int(11) NOT NULL,
  `status` enum('on','off','maintenance') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `drug`
--

CREATE TABLE `drug` (
  `id` varchar(10) NOT NULL,
  `name` varchar(100) NOT NULL,
  `stock` int(11) NOT NULL,
  `reorder` int(11) NOT NULL,
  `status` enum('available','reorder','out-of-stock') NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `updated_at` datetime DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `emergency_alert`
--

CREATE TABLE `emergency_alert` (
  `id` int(11) NOT NULL,
  `code` varchar(50) NOT NULL,
  `color` varchar(20) DEFAULT '#e74c3c',
  `dept` varchar(50) DEFAULT 'General',
  `time` datetime NOT NULL,
  `status` enum('Active','Resolved') DEFAULT 'Active'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `emergency_alert`
--

INSERT INTO `emergency_alert` (`id`, `code`, `color`, `dept`, `time`, `status`) VALUES
(1, 'Code Green', 'green', 'General', '2025-06-13 22:54:01', 'Resolved'),
(2, 'Code Blue', '#e74c3c', 'General', '2025-06-13 22:54:04', 'Resolved'),
(3, 'Red', 'Red', 'General', '2025-06-13 23:07:55', 'Resolved'),
(7, 'Code Blue', '#3498db', 'General', '2025-06-13 23:11:26', 'Active'),
(8, 'Code Orange', '#e67e22', 'General', '2025-06-15 17:27:28', 'Resolved');

-- --------------------------------------------------------

--
-- Table structure for table `notification`
--

CREATE TABLE `notification` (
  `id` int(11) NOT NULL,
  `message` varchar(200) NOT NULL,
  `priority` enum('low','medium','high','critical') NOT NULL,
  `department` varchar(100) DEFAULT NULL,
  `timestamp` datetime NOT NULL DEFAULT current_timestamp(),
  `status` enum('sent','read','archived') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `ot`
--

CREATE TABLE `ot` (
  `ot_id` int(11) NOT NULL,
  `surgeon` varchar(100) NOT NULL,
  `procedures` varchar(255) NOT NULL,
  `time` varchar(50) NOT NULL,
  `status` varchar(50) DEFAULT 'Scheduled'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `ot`
--

INSERT INTO `ot` (`ot_id`, `surgeon`, `procedures`, `time`, `status`) VALUES
(1, 'Sample', 'Sample', '2:90', 'Completed'),
(2, 'Sample', 'Sample', '2:90', 'Scheduled'),
(3, 'Sample', 'Sample', '2:90', 'Scheduled');

-- --------------------------------------------------------

--
-- Table structure for table `ot_schedule`
--

CREATE TABLE `ot_schedule` (
  `id` int(11) NOT NULL,
  `patient_name` varchar(100) DEFAULT NULL,
  `surgeon_name` varchar(100) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `scheduled_date` date DEFAULT NULL,
  `scheduled_time` time DEFAULT NULL,
  `status` varchar(50) DEFAULT 'Scheduled'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `ot_schedule`
--

INSERT INTO `ot_schedule` (`id`, `patient_name`, `surgeon_name`, `description`, `scheduled_date`, `scheduled_time`, `status`) VALUES
(1, 'new', 'Dr', 'Sample ', '2025-06-14', '05:13:00', 'Completed');

-- --------------------------------------------------------

--
-- Table structure for table `patient_queue`
--

CREATE TABLE `patient_queue` (
  `id` int(11) NOT NULL,
  `patient_name` varchar(100) DEFAULT NULL,
  `department_id` int(11) DEFAULT NULL,
  `doctor_or_surgeon` varchar(100) DEFAULT NULL,
  `token_number` int(11) DEFAULT NULL,
  `scheduled_time` datetime DEFAULT NULL,
  `status` varchar(50) DEFAULT 'Waiting'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `patient_queue`
--

INSERT INTO `patient_queue` (`id`, `patient_name`, `department_id`, `doctor_or_surgeon`, `token_number`, `scheduled_time`, `status`) VALUES
(1, 'new', 1, 'Dr', 1, '2025-06-13 23:56:00', 'Completed'),
(2, 'new', 1, 'Dr', 2, '2025-06-13 23:58:00', 'In Progress'),
(3, 'new', 2, 'Dr', 1, '2025-06-14 00:50:00', 'Completed'),
(4, 'new', 2, 'Dr', 2, '2025-06-14 02:54:00', 'Completed'),
(5, 'new', 2, 'Dr', 3, '2025-06-14 01:23:00', 'Completed'),
(6, 'new', 2, 'Dr', 4, '2025-06-14 01:23:00', 'Completed'),
(7, 'new', 2, 'Dr', 5, '2025-06-15 17:55:00', 'In Progress');

-- --------------------------------------------------------

--
-- Table structure for table `pharmacy`
--

CREATE TABLE `pharmacy` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `stock` int(11) NOT NULL,
  `reorder_level` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `pharmacy`
--

INSERT INTO `pharmacy` (`id`, `name`, `stock`, `reorder_level`) VALUES
(1, 'Paracetamol', 50, 20),
(2, 'Ibuprofen', 10, 15),
(3, 'Amoxicillin', 20, 10),
(4, 'Cetrizine', 30, 25),
(5, 'Metformin', 5, 10),
(6, 'Aspirin', 15, 5),
(7, 'Vitamin D3', 60, 30),
(8, 'Sample', 47, 10),
(9, 'Paracetom', 100, 30);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `password` varchar(255) NOT NULL,
  `role` enum('admin','blood_bank','receptionist','pharmacy') NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`id`, `username`, `password`, `role`, `created_at`) VALUES
(1, 'admin1', 'admin123', 'admin', '2025-06-15 10:59:51'),
(2, 'bloodstaff1', 'blood123', 'blood_bank', '2025-06-15 10:59:51'),
(3, 'reception1', 'recept123', 'receptionist', '2025-06-15 10:59:51'),
(4, 'pharma1', 'pharma123', 'pharmacy', '2025-06-15 10:59:51');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `activity_log`
--
ALTER TABLE `activity_log`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `blood_bank`
--
ALTER TABLE `blood_bank`
  ADD PRIMARY KEY (`blood_id`);

--
-- Indexes for table `broadcast_message`
--
ALTER TABLE `broadcast_message`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `code_definitions`
--
ALTER TABLE `code_definitions`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `consultation_schedule`
--
ALTER TABLE `consultation_schedule`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `consultation_tokens`
--
ALTER TABLE `consultation_tokens`
  ADD PRIMARY KEY (`token_id`),
  ADD KEY `consultation_id` (`consultation_id`);

--
-- Indexes for table `departments`
--
ALTER TABLE `departments`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `display_screen`
--
ALTER TABLE `display_screen`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `drug`
--
ALTER TABLE `drug`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `emergency_alert`
--
ALTER TABLE `emergency_alert`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `notification`
--
ALTER TABLE `notification`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `ot`
--
ALTER TABLE `ot`
  ADD PRIMARY KEY (`ot_id`);

--
-- Indexes for table `ot_schedule`
--
ALTER TABLE `ot_schedule`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `patient_queue`
--
ALTER TABLE `patient_queue`
  ADD PRIMARY KEY (`id`),
  ADD KEY `department_id` (`department_id`);

--
-- Indexes for table `pharmacy`
--
ALTER TABLE `pharmacy`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `activity_log`
--
ALTER TABLE `activity_log`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=48;

--
-- AUTO_INCREMENT for table `blood_bank`
--
ALTER TABLE `blood_bank`
  MODIFY `blood_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `broadcast_message`
--
ALTER TABLE `broadcast_message`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `code_definitions`
--
ALTER TABLE `code_definitions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `consultation_schedule`
--
ALTER TABLE `consultation_schedule`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `consultation_tokens`
--
ALTER TABLE `consultation_tokens`
  MODIFY `token_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `departments`
--
ALTER TABLE `departments`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `display_screen`
--
ALTER TABLE `display_screen`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `emergency_alert`
--
ALTER TABLE `emergency_alert`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `notification`
--
ALTER TABLE `notification`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `ot`
--
ALTER TABLE `ot`
  MODIFY `ot_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `ot_schedule`
--
ALTER TABLE `ot_schedule`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `patient_queue`
--
ALTER TABLE `patient_queue`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `pharmacy`
--
ALTER TABLE `pharmacy`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `consultation_tokens`
--
ALTER TABLE `consultation_tokens`
  ADD CONSTRAINT `consultation_tokens_ibfk_1` FOREIGN KEY (`consultation_id`) REFERENCES `consultation_schedule` (`id`) ON DELETE CASCADE;

--
-- Constraints for table `patient_queue`
--
ALTER TABLE `patient_queue`
  ADD CONSTRAINT `patient_queue_ibfk_1` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
