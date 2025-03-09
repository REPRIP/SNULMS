-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Mar 09, 2025 at 01:24 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `snulms`
--

-- --------------------------------------------------------

--
-- Table structure for table `admin`
--

CREATE TABLE `admin` (
  `ID` int(11) NOT NULL,
  `AdminID` int(11) NOT NULL,
  `LastAccess` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Dumping data for table `admin`
--

INSERT INTO `admin` (`ID`, `AdminID`, `LastAccess`) VALUES
(0, 1, NULL);

-- --------------------------------------------------------

--
-- Table structure for table `coursecontent`
--

CREATE TABLE `coursecontent` (
  `CourseContentID` int(11) NOT NULL,
  `CCName` varchar(200) NOT NULL,
  `Description` mediumtext DEFAULT NULL,
  `FileUrl` text DEFAULT NULL,
  `UploadDate` date NOT NULL,
  `IsAssignment` tinyint(1) DEFAULT NULL,
  `CourseID` varchar(20) NOT NULL,
  `UploadedBy` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Dumping data for table `coursecontent`
--

INSERT INTO `coursecontent` (`CourseContentID`, `CCName`, `Description`, `FileUrl`, `UploadDate`, `IsAssignment`, `CourseID`, `UploadedBy`) VALUES
(1, 'UNIT 1', 'STUDY ON YOUR OWN!', 'Nil', '2025-03-01', 0, 'CS2004', 2),
(2, 'UNIT 2', 'MIDSEM PORTION', 'NIL', '2025-03-01', 0, 'CS2004', 2),
(3, 'UNIT 1', 'ER DIAGRAMS', 'NIL', '2025-03-01', 0, 'CS2001T', 1);

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `CourseID` varchar(20) NOT NULL,
  `CourseName` varchar(100) NOT NULL,
  `CourseCredit` int(11) NOT NULL,
  `Category` varchar(50) DEFAULT NULL,
  `SemesterNo` int(11) NOT NULL,
  `FacultyID` int(11) NOT NULL,
  `DepartmentID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`CourseID`, `CourseName`, `CourseCredit`, `Category`, `SemesterNo`, `FacultyID`, `DepartmentID`) VALUES
('CS2001T', 'DataBase Management Systems', 3, 'Core', 4, 1, 1),
('CS2004', 'Design and Analysis of Algorithms', 3, 'Core', 4, 2, 1);

-- --------------------------------------------------------

--
-- Table structure for table `department`
--

CREATE TABLE `department` (
  `DepartmentID` int(11) NOT NULL,
  `DepartmentName` varchar(100) NOT NULL,
  `HODName` varchar(100) NOT NULL,
  `UniversityID` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Dumping data for table `department`
--

INSERT INTO `department` (`DepartmentID`, `DepartmentName`, `HODName`, `UniversityID`) VALUES
(1, 'CSE', 'CSEHOD', 0),
(2, 'COMMERCE', 'COMMERCEHOD', 0);

-- --------------------------------------------------------

--
-- Table structure for table `faculty`
--

CREATE TABLE `faculty` (
  `ID` int(11) NOT NULL,
  `FacultyID` int(11) NOT NULL,
  `PhoneNo` int(10) NOT NULL,
  `Qualification` varchar(200) NOT NULL,
  `Level` varchar(100) NOT NULL,
  `DepartmentID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Dumping data for table `faculty`
--

INSERT INTO `faculty` (`ID`, `FacultyID`, `PhoneNo`, `Qualification`, `Level`, `DepartmentID`) VALUES
(1, 1, 1234567890, 'Ph.D(Computer Networks) ', 'Assistant Professor', 1),
(2, 2, 1234567890, 'Ph.D. in Information and Communication Engineering', 'Professor', 1);

-- --------------------------------------------------------

--
-- Table structure for table `student`
--

CREATE TABLE `student` (
  `ID` int(11) NOT NULL,
  `RegistrationNo` int(11) NOT NULL,
  `PhoneNo` int(10) NOT NULL,
  `Class` varchar(50) NOT NULL,
  `DoB` date NOT NULL,
  `Semester` varchar(50) NOT NULL,
  `DepartmentID` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Dumping data for table `student`
--

INSERT INTO `student` (`ID`, `RegistrationNo`, `PhoneNo`, `Class`, `DoB`, `Semester`, `DepartmentID`) VALUES
(3, 157, 1234567890, 'AI & DS B', '2005-12-12', '4', 1),
(4, 165, 2147483647, 'AI & DS B', '2005-12-20', '4', 1);

-- --------------------------------------------------------

--
-- Table structure for table `university`
--

CREATE TABLE `university` (
  `UniveristyID` int(11) NOT NULL,
  `UniversityName` varchar(100) NOT NULL,
  `Address` varchar(200) NOT NULL,
  `City` varchar(100) NOT NULL,
  `State` varchar(100) NOT NULL,
  `Pincode` int(6) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Dumping data for table `university`
--

INSERT INTO `university` (`UniveristyID`, `UniversityName`, `Address`, `City`, `State`, `Pincode`) VALUES
(0, 'Shiv Nadar University Chennai', 'Kalvakkam', 'Chennai', 'Tamil Nadu', 603105);

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `ID` int(11) NOT NULL,
  `UserName` varchar(100) NOT NULL,
  `FirstName` varchar(100) NOT NULL,
  `LastName` varchar(100) DEFAULT NULL,
  `Role` enum('admin','faculty','student','') NOT NULL,
  `Email` varchar(50) DEFAULT NULL,
  `PasswordHash` varchar(500) NOT NULL,
  `CreatedOn` date NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`ID`, `UserName`, `FirstName`, `LastName`, `Role`, `Email`, `PasswordHash`, `CreatedOn`) VALUES
(0, 'admin', 'admin', '', 'admin', 'admin@snulms.com', 'scrypt:32768:8:1$DCCnBWhqdyDSpYVL$1ad2514490dc829a185465200632b0fb9d20b54b20fe39d1b9dcd4db8108fb8f2d3fdbd37112fbb796880fb5c8ee74c43d9cc70cae0db5cd88c514971cc47441', '2025-03-08'),
(1, 'Veeramani', 'Veeramani', 'S', 'faculty', 'veeramani@snulms.com', 'scrypt:32768:8:1$8na9olEKLCgdRcmu$0996dd26e77adc7ab04045982498e7c581de110411b77a2277e2c4dcd549b9cc6a5ca46190ce9f3a981cc500355f4e0874ae4f2eab104336ec370a8b14bd03ee', '2025-03-08'),
(2, 'Milton', 'Milton', 'RS', 'faculty', 'rsmilton@snulms.com', 'scrypt:32768:8:1$Xqp3bNYc9dZmZHlu$577b8c06c670549e79c6766239f9f145ca4231386919568bca732bea853635667ed4b29638d66c5277bfcb19c7919dd05472af116e3407ddfc8aae2f56a356a1', '2025-03-08'),
(3, 'Vignesh', 'Vignesh', 'V', 'student', 'vignesh@snulms.com', 'scrypt:32768:8:1$Z3P4CegSs2xK6Rcg$c4161379478a6cc373cef06986510d93aa851f756c53903266a25d74ee9a8d11a26a6ab34de1b40da2e8bf1bae4f4591a54f440bb84cdd9084b01e0bf6b80dbc', '2025-03-08'),
(4, 'Vivesh', 'Vivesh', 'G', 'student', 'vivesh@snulms.com', 'scrypt:32768:8:1$UwITrHrhySZuBDeD$fd5c4d06ba455ba143ee4bf96ca512130ca589ecb7a0d85ae5073daa09fc34144f09870561f340899bd161efb89bc1e4e59918b17eddedd5969588d4b0bbdf39', '2025-03-09');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `admin`
--
ALTER TABLE `admin`
  ADD PRIMARY KEY (`AdminID`),
  ADD KEY `ID` (`ID`);

--
-- Indexes for table `coursecontent`
--
ALTER TABLE `coursecontent`
  ADD PRIMARY KEY (`CourseContentID`),
  ADD KEY `UploadedBy` (`UploadedBy`),
  ADD KEY `CourseID` (`CourseID`);

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`CourseID`),
  ADD UNIQUE KEY `CourseID` (`CourseID`),
  ADD KEY `DepartmentID` (`DepartmentID`),
  ADD KEY `FacultyID` (`FacultyID`);

--
-- Indexes for table `department`
--
ALTER TABLE `department`
  ADD PRIMARY KEY (`DepartmentID`),
  ADD KEY `UniversityID` (`UniversityID`);

--
-- Indexes for table `faculty`
--
ALTER TABLE `faculty`
  ADD PRIMARY KEY (`FacultyID`),
  ADD KEY `ID` (`ID`),
  ADD KEY `DepartmentID` (`DepartmentID`);

--
-- Indexes for table `student`
--
ALTER TABLE `student`
  ADD PRIMARY KEY (`RegistrationNo`),
  ADD KEY `ID` (`ID`),
  ADD KEY `DepartmentID` (`DepartmentID`);

--
-- Indexes for table `university`
--
ALTER TABLE `university`
  ADD PRIMARY KEY (`UniveristyID`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`ID`),
  ADD UNIQUE KEY `Email` (`Email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `admin`
--
ALTER TABLE `admin`
  MODIFY `AdminID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `coursecontent`
--
ALTER TABLE `coursecontent`
  MODIFY `CourseContentID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `department`
--
ALTER TABLE `department`
  MODIFY `DepartmentID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `faculty`
--
ALTER TABLE `faculty`
  MODIFY `FacultyID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT for table `student`
--
ALTER TABLE `student`
  MODIFY `RegistrationNo` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=166;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `admin`
--
ALTER TABLE `admin`
  ADD CONSTRAINT `admin_ibfk_1` FOREIGN KEY (`ID`) REFERENCES `users` (`ID`);

--
-- Constraints for table `coursecontent`
--
ALTER TABLE `coursecontent`
  ADD CONSTRAINT `coursecontent_ibfk_1` FOREIGN KEY (`UploadedBy`) REFERENCES `faculty` (`FacultyID`),
  ADD CONSTRAINT `coursecontent_ibfk_2` FOREIGN KEY (`CourseID`) REFERENCES `courses` (`CourseID`);

--
-- Constraints for table `courses`
--
ALTER TABLE `courses`
  ADD CONSTRAINT `courses_ibfk_1` FOREIGN KEY (`DepartmentID`) REFERENCES `department` (`DepartmentID`),
  ADD CONSTRAINT `courses_ibfk_2` FOREIGN KEY (`FacultyID`) REFERENCES `faculty` (`FacultyID`);

--
-- Constraints for table `department`
--
ALTER TABLE `department`
  ADD CONSTRAINT `department_ibfk_1` FOREIGN KEY (`UniversityID`) REFERENCES `university` (`UniveristyID`);

--
-- Constraints for table `faculty`
--
ALTER TABLE `faculty`
  ADD CONSTRAINT `faculty_ibfk_1` FOREIGN KEY (`ID`) REFERENCES `users` (`ID`),
  ADD CONSTRAINT `faculty_ibfk_2` FOREIGN KEY (`DepartmentID`) REFERENCES `department` (`DepartmentID`);

--
-- Constraints for table `student`
--
ALTER TABLE `student`
  ADD CONSTRAINT `student_ibfk_1` FOREIGN KEY (`ID`) REFERENCES `users` (`ID`),
  ADD CONSTRAINT `student_ibfk_2` FOREIGN KEY (`DepartmentID`) REFERENCES `department` (`DepartmentID`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
