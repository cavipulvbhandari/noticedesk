package com.noticedesk.api.service.storage;

import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.core.sync.RequestBody;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.GetObjectRequest;
import software.amazon.awssdk.services.s3.model.HeadObjectRequest;
import software.amazon.awssdk.services.s3.model.NoSuchKeyException;
import software.amazon.awssdk.services.s3.model.PutObjectRequest;
import software.amazon.awssdk.services.s3.model.S3Exception;
import software.amazon.awssdk.services.s3.model.ServerSideEncryption;

/**
 * AWS S3 backed storage using the AWS SDK v2 synchronous client.
 *
 * <p>All objects are stored with AES256 server-side encryption.
 * The {@link S3Client} is supplied by {@link StorageFactory} so it can be
 * mocked in tests without hitting AWS.
 */
@Slf4j
public class S3StorageService implements StorageService {

    private final S3Client s3Client;
    private final String bucket;

    public S3StorageService(S3Client s3Client, String bucket) {
        this.s3Client = s3Client;
        this.bucket = bucket;
    }

    @Override
    public String store(byte[] data, String key, String contentType) {
        try {
            PutObjectRequest.Builder builder = PutObjectRequest.builder()
                    .bucket(bucket)
                    .key(key)
                    .contentLength((long) data.length)
                    .serverSideEncryption(ServerSideEncryption.AES256);
            if (contentType != null && !contentType.isBlank()) {
                builder.contentType(contentType);
            }
            s3Client.putObject(builder.build(), RequestBody.fromBytes(data));
            log.debug("s3_stored bucket={} key={} bytes={}", bucket, key, data.length);
            return key;
        } catch (S3Exception e) {
            throw new RuntimeException("S3 put_object failed for key='" + key + "': " + e.getMessage(), e);
        }
    }

    @Override
    public byte[] retrieve(String key) {
        try {
            return s3Client.getObjectAsBytes(
                    GetObjectRequest.builder().bucket(bucket).key(key).build()
            ).asByteArray();
        } catch (NoSuchKeyException e) {
            throw new RuntimeException("Object not found in S3: " + key, e);
        } catch (S3Exception e) {
            throw new RuntimeException("S3 get_object failed for key='" + key + "': " + e.getMessage(), e);
        }
    }

    @Override
    public boolean exists(String key) {
        try {
            s3Client.headObject(HeadObjectRequest.builder().bucket(bucket).key(key).build());
            return true;
        } catch (NoSuchKeyException e) {
            return false;
        } catch (S3Exception e) {
            log.warn("s3_head_object_failed bucket={} key={} error={}", bucket, key, e.getMessage());
            return false;
        }
    }
}
