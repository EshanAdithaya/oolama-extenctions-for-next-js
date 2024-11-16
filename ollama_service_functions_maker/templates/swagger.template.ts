import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';

export const {{ entity.name }}SwaggerDocs = {
    tags: [
        {
            name: '{{ entity.name }}',
            description: 'Operations related to {{ entity.name }}'
        }
    ],
    schemas: {
        Create{{ entity.name }}Dto: {
            type: 'object',
            properties: {
                {% for prop in entity.properties %}
                {{ prop.name }}: {
                    type: '{{ prop.type }}',
                    description: '{{ prop.description }}'
                }{% if not loop.last %},{% endif %}
                {% endfor %}
            },
            required: [
                {% for prop in entity.properties if prop.required %}
                '{{ prop.name }}'{% if not loop.last %},{% endif %}
                {% endfor %}
            ]
        }
    }
};
