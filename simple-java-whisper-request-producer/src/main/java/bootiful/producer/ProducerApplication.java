package bootiful.producer;

import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.amqp.core.*;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.util.SystemPropertyUtils;

import java.nio.charset.Charset;
import java.util.Map;
import java.util.Objects;

@SpringBootApplication
public class ProducerApplication {

    private final ObjectMapper objectMapper;

    ProducerApplication(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
    }

    private String json(Object o) {
        try {
            return this.objectMapper.writeValueAsString(o);
        } catch (Throwable throwable) {
            //
        }
        return null;
    }

    @Bean
    ApplicationRunner applicationRunner(AmqpAdmin amqpAdmin, AmqpTemplate template) {
        return args -> {
            var requests = "transcription-requests";
            var key = requests;
            var q = QueueBuilder.durable(requests).build();
            var exchange = ExchangeBuilder
                    .directExchange(requests)
                    .durable(true)
                    .build();
            var binding = BindingBuilder
                    .bind(q)
                    .to(exchange)
                    .with(key)
                    .noargs();
            amqpAdmin.declareQueue(q);
            amqpAdmin.declareExchange(exchange);
            amqpAdmin.declareBinding(binding);
            var json = this.json(Map.of("path", SystemPropertyUtils.resolvePlaceholders("${HOME}/Desktop/audio.mp3")));
            var build = MessageBuilder
                    .withBody(Objects.requireNonNull(json).getBytes(Charset.defaultCharset()))
                    .build();
            var replyMessage = template.sendAndReceive(requests, build);
            var replyBytes = replyMessage.getBody();
            var reply = new String(replyBytes);
            System.out.println("got the transcript: " + reply);


        };
    }

    public static void main(String[] args) {
        SpringApplication.run(ProducerApplication.class, args);
    }

}
