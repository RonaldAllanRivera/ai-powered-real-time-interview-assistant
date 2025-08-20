<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\AiController;

Route::get('/health', [AiController::class, 'health']);
Route::post('/generate-answer', [AiController::class, 'generate']);
Route::post('/transcripts', [AiController::class, 'storeTranscript']);
