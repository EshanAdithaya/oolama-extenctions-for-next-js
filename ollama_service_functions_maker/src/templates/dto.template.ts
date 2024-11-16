import { ApiProperty } from '@nestjs/swagger';

export class Create{{ entity.name }}Dto {
    {% for prop in entity.properties %}
    @ApiProperty({
        description: '{{ prop.description }}',
        required: {{ prop.required }},
        type: () => {{ prop.type }}
    })
    {{ prop.name }}{% if not prop.required %}?{% endif %}: {{ prop.type }};
    {% endfor %}
}

export class Update{{ entity.name }}Dto extends Partial<Create{{ entity.name }}Dto> {}

export class {{ entity.name }}ResponseDto extends Create{{ entity.name }}Dto {
    @ApiProperty({ description: 'Entity ID' })
    id: string;

    @ApiProperty({ description: 'Creation timestamp' })
    createdAt: Date;

    @ApiProperty({ description: 'Last update timestamp' })
    updatedAt: Date;
}