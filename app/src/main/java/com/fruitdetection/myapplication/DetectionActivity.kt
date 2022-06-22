package com.fruitdetection.myapplication

import android.app.Activity
import android.content.Intent
import android.net.Uri
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import android.widget.Toast
import androidx.activity.result.ActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContentProviderCompat.requireContext
import com.bumptech.glide.Glide
import com.fruitdetection.myapplication.databinding.ActivityDetectionBinding
import com.github.dhaval2404.imagepicker.ImagePicker
import java.io.File

class DetectionActivity : AppCompatActivity() {
    private lateinit var binding: ActivityDetectionBinding
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityDetectionBinding.inflate(layoutInflater)
        setContentView(binding.root)

        binding.ivUpload.setOnClickListener {
            openImagePicker()
        }
        binding.btnDeteksi.setOnClickListener {
            startActivity(Intent(this,ResultActivity::class.java))
        }
    }

    private val startForProfileImageResult =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { result: ActivityResult ->
            val resultCode = result.resultCode
            val data = result.data
            when (resultCode) {
                Activity.RESULT_OK -> {
                    val fileUri = data?.data
                    fileUri?.let { loadImage(it) }
                }
                ImagePicker.RESULT_ERROR -> {
                    Toast.makeText(
                        this,
                        ImagePicker.getError(data),
                        Toast.LENGTH_SHORT
                    )
                        .show()
                }
                else -> {

                }
            }
        }

    private fun loadImage(uri: Uri) {
        binding.apply {
            Glide.with(binding.root)
                .load(uri)
                .into(ivUpload)

        }
    }

    private fun openImagePicker() {
        ImagePicker.with(this)
            .crop()
            .saveDir(
                File(
                    this.externalCacheDir,
                    "ImagePicker"
                )
            )
            .compress(1024)
            .maxResultSize(
                1080,
                1080
            )
            .createIntent { intent ->
                startForProfileImageResult.launch(intent)
            }
    }
}