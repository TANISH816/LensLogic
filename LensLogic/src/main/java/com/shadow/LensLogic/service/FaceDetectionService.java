package com.shadow.LensLogic.service;

import org.opencv.core.*;
import org.opencv.dnn.Dnn;
import org.opencv.dnn.Net;
import org.opencv.imgcodecs.Imgcodecs;
import org.opencv.imgproc.Imgproc;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import jakarta.annotation.PostConstruct;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.List;

@Service
public class FaceDetectionService {

    private Net faceNet;

    static {
        // Java 21 requires a slightly different approach for loading native shared libs
        try {
            nu.pattern.OpenCV.loadLocally();
        } catch (Exception e) {
            // Fallback for different OS environments
            System.loadLibrary(org.opencv.core.Core.NATIVE_LIBRARY_NAME);
        }
    }

    @PostConstruct
    public void init() throws IOException {
        // OpenCV cannot read directly from a JAR/Resource stream easily,
        // so we copy them to a temp file for the DNN to read.
        Path protoPath = loadResourceToTemp("models/deploy.prototxt");
        Path modelPath = loadResourceToTemp("models/res10_300x300_ssd_iter_140000.caffemodel");

        this.faceNet = Dnn.readNetFromCaffe(
                protoPath.toAbsolutePath().toString(),
                modelPath.toAbsolutePath().toString()
        );
    }

    private Path loadResourceToTemp(String path) throws IOException {
        ClassPathResource resource = new ClassPathResource(path);
        Path tempFile = Files.createTempFile("model_", "_" + resource.getFilename());
        Files.copy(resource.getInputStream(), tempFile, StandardCopyOption.REPLACE_EXISTING);
        return tempFile;
    }

    public byte[] processFaceDetection(MultipartFile file) throws IOException {
        // 1. Convert MultipartFile to OpenCV Mat
        Mat image = Imgcodecs.imdecode(new MatOfByte(file.getBytes()), Imgcodecs.IMREAD_UNCHANGED);

        if (image.empty()) {
            throw new IOException("Could not decode image");
        }

        int frameHeight = image.rows();
        int frameWidth = image.cols();

        System.out.println(frameHeight + " " + frameWidth);

        // 2. Pre-process: Resize to 300x300 and apply Mean Subtraction
        // Scalar(104, 177, 123) is the standard BGR mean for this ResNet model
//        Mat blob = Dnn.blobFromImage(image, 1.0, new Size(300, 300),
//                new Scalar(104.0, 177.0, 123.0), false, false);

        // Ensure the 'swapRB' parameter (the second to last one) is FALSE
//        Mat blob = Dnn.blobFromImage(image, 1.0, new Size(300, 300),
//                new Scalar(104.0, 177.0, 123.0), false, false);

        // 1. Force the image to BGR (removes Alpha channel if it's a PNG)
        if (image.channels() == 4) {
            Imgproc.cvtColor(image, image, Imgproc.COLOR_BGRA2BGR);
        }

        // 2. Try these NEW parameters for the blob
        // Scale: 1.0 (sometimes 0.007843 if using a different model version)
        // Size: 300, 300 (standard for SSD)
        // Mean: (104.0, 117.0, 123.0) - Standard BGR means
        // swapRB: false (The model wants BGR, and OpenCV reads BGR, so don't swap)
        Mat blob = Dnn.blobFromImage(image, 1.0, new Size(300, 300),
                new Scalar(104.0, 117.0, 123.0), false, false);
        faceNet.setInput(blob);

        // 3. Inference (Forward Pass)
        Mat detections = faceNet.forward();

        // 4. Parse Detections
        // The output is a 4D Mat [1, 1, N, 7] -> we reshape to [N, 7] for easier access
        Mat detectionMat = detections.reshape(1, (int) detections.total() / 7);

        for (int i = 0; i < detectionMat.rows(); i++) {
            double confidence = detectionMat.get(i, 2)[0];
            System.out.println("Detection " + i + " confidence: " + confidence);

            int x1 = (int) (detectionMat.get(i, 3)[0] * frameWidth);
            int y1 = (int) (detectionMat.get(i, 4)[0] * frameHeight);
            int x2 = (int) (detectionMat.get(i, 5)[0] * frameWidth);
            int y2 = (int) (detectionMat.get(i, 6)[0] * frameHeight);

//            int x1 = Math.max(0, Math.min((int) (detectionMat.get(i, 3)[0] * frameWidth), frameWidth - 1));
//            int y1 = Math.max(0, Math.min((int) (detectionMat.get(i, 4)[0] * frameWidth), frameHeight - 1));
//            int x2 = Math.max(0, Math.min((int) (detectionMat.get(i, 5)[0] * frameWidth), frameWidth - 1));
//            int y2 = Math.max(0, Math.min((int) (detectionMat.get(i, 6)[0] * frameWidth), frameHeight - 1));

            // Only process detections above 50% confidence
            if (confidence > 0.10 && (frameWidth / 10) < Math.abs(x2 - x1) && (frameHeight / 10) < Math.abs(y2 - y1)) {
                // The model returns normalized coordinates (0.0 to 1.0)

                System.out.println("(frameWidth / 10) : " + (frameWidth / 10) + " Math.abs(x2 - x1) : " + Math.abs(x2 - x1) +  " (frameHeight / 10) : " + (frameHeight / 10) + " Math.abs(y2 - y1) : " +  Math.abs(y2 - y1) );
                System.out.println(x1 +" "+ y1 +" "+ x2 +" "+ y2);

                // Draw bounding box
                Imgproc.rectangle(image, new Point(x1, y1), new Point(x2, y2),
                        new Scalar(0, 255, 0), 2);

                // Draw confidence label
                String label = String.format("%.2f%%", confidence * 100);
                Imgproc.putText(image, label, new Point(x1, y1 - 10),
                        Imgproc.FONT_HERSHEY_SIMPLEX, 0.6, new Scalar(0, 255, 0), 2);
            }
        }

        // 5. Convert back to JPG for the front-end
        MatOfByte buffer = new MatOfByte();
        Imgcodecs.imencode(".jpg", image, buffer);

        // Cleanup memory
        blob.release();
        detections.release();
        detectionMat.release();
        image.release();

        return buffer.toArray();
    }


}

