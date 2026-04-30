package com.shadow.LensLogic;

import jakarta.annotation.PostConstruct;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

//@SpringBootApplication
@SpringBootApplication(exclude = {
        org.springframework.ai.vectorstore.pgvector.autoconfigure.PgVectorStoreAutoConfiguration.class
})
public class LensLogicApplication {

	public static void main(String[] args) {
		SpringApplication.run(LensLogicApplication.class, args);
	}

    @PostConstruct
    public void init() {
        // This loads the shared OpenCV library into your JVM
        nu.pattern.OpenCV.loadShared(); //[cite: 52]
    }

}
