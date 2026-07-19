package com.noticedesk.api.config;

import org.apache.coyote.ProtocolHandler;
import org.springframework.boot.web.embedded.tomcat.TomcatProtocolHandlerCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.concurrent.Executors;

/**
 * Enable Java 21 virtual threads for Tomcat, giving throughput comparable to
 * FastAPI's async I/O without WebFlux complexity.
 */
@Configuration
public class VirtualThreadConfig {

    @Bean
    public TomcatProtocolHandlerCustomizer<?> virtualThreadProtocolHandlerCustomizer() {
        return (ProtocolHandler protocolHandler) ->
                protocolHandler.setExecutor(Executors.newVirtualThreadPerTaskExecutor());
    }
}
