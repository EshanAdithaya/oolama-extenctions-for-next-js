import { 
    Controller, Get, Post, Put, Delete, Body, Param, 
    UseGuards, ValidationPipe, ParseUUIDPipe 
} from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { {{ entity.name }}Service } from '../services/{{ entity.name.lower() }}.service';
import { 
    Create{{ entity.name }}Dto, 
    Update{{ entity.name }}Dto,
    {{ entity.name }}ResponseDto 
} from '../dtos/{{ entity.name.lower() }}.dto';

@ApiTags('{{ entity.name }}')
@Controller('{{ entity.name.lower() }}')
export class {{ entity.name }}Controller {
    constructor(private readonly service: {{ entity.name }}Service) {}

    @Post()
    @ApiOperation({ summary: 'Create {{ entity.name }}' })
    @ApiResponse({ status: 201, type: {{ entity.name }}ResponseDto })
    async create(@Body(ValidationPipe) data: Create{{ entity.name }}Dto) {
        return this.service.create(data);
    }

    @Get()
    @ApiOperation({ summary: 'Get all {{ entity.name }}s' })
    @ApiResponse({ status: 200, type: [{{ entity.name }}ResponseDto] })
    async findAll() {
        return this.service.findAll();
    }

    @Get(':id')
    @ApiOperation({ summary: 'Get {{ entity.name }} by id' })
    @ApiResponse({ status: 200, type: {{ entity.name }}ResponseDto })
    async findOne(@Param('id', ParseUUIDPipe) id: string) {
        return this.service.findOne(id);
    }

    @Put(':id')
    @ApiOperation({ summary: 'Update {{ entity.name }}' })
    @ApiResponse({ status: 200, type: {{ entity.name }}ResponseDto })
    async update(
        @Param('id', ParseUUIDPipe) id: string,
        @Body(ValidationPipe) data: Update{{ entity.name }}Dto
    ) {
        return this.service.update(id, data);
    }

    @Delete(':id')
    @ApiOperation({ summary: 'Delete {{ entity.name }}' })
    @ApiResponse({ status: 200, type: {{ entity.name }}ResponseDto })
    async delete(@Param('id', ParseUUIDPipe) id: string) {
        return this.service.delete(id);
    }
}
