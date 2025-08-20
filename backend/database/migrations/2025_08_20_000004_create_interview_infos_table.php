<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration {
    public function up(): void
    {
        Schema::create('interview_infos', function (Blueprint $table) {
            $table->id();
            $table->string('session_id', 100)->unique();
            $table->string('company', 150)->nullable();
            $table->string('role', 150)->nullable();
            $table->longText('context')->nullable(); // job description, notes, requirements
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('interview_infos');
    }
};
