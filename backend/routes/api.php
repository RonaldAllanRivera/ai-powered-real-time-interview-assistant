<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\Api\AiController;

Route::get('/health', [AiController::class, 'health']);
Route::post('/generate-answer', [AiController::class, 'generate']);
Route::post('/transcripts', [AiController::class, 'storeTranscript']);
Route::get('/personas', [AiController::class, 'personas']);
Route::get('/interview-info', [AiController::class, 'getInterviewInfo']);
Route::post('/interview-info', [AiController::class, 'upsertInterviewInfo']);
