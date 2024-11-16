import { Injectable } from '@nestjs/common';
import { PrismaService } from '../prisma.service';
import { Create{{ entity.name }}Dto, Update{{ entity.name }}Dto } from '../dtos/{{ entity.name.lower() }}.dto';

@Injectable()
export class {{ entity.name }}Service {
    constructor(private prisma: PrismaService) {}

    async create(data: Create{{ entity.name }}Dto) {
        return this.prisma.{{ entity.name.lower() }}.create({ data });
    }

    async findAll() {
        return this.prisma.{{ entity.name.lower() }}.findMany();
    }

    async findOne(id: string) {
        return this.prisma.{{ entity.name.lower() }}.findUnique({
            where: { id }
        });
    }

    async update(id: string, data: Update{{ entity.name }}Dto) {
        return this.prisma.{{ entity.name.lower() }}.update({
            where: { id },
            data
        });
    }

    async delete(id: string) {
        return this.prisma.{{ entity.name.lower() }}.delete({
            where: { id }
        });
    }
}