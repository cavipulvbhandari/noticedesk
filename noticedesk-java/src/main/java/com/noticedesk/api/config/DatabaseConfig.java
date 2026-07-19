package com.noticedesk.api.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.namedparam.NamedParameterJdbcTemplate;

import javax.sql.DataSource;

@Configuration
public class DatabaseConfig {

    /**
     * NamedParameterJdbcTemplate is Spring's equivalent of SQLAlchemy's
     * session.execute(text("... :param ..."), {"param": value}) pattern.
     * All controllers/services inject this directly.
     */
    @Bean
    public NamedParameterJdbcTemplate namedParameterJdbcTemplate(DataSource dataSource) {
        return new NamedParameterJdbcTemplate(dataSource);
    }
}
