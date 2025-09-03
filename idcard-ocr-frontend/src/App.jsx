// src/App.jsx
import React, { useState } from "react";
import {
  Grid,
  Typography,
  Button,
  CircularProgress,
  Paper,
  Box,
} from "@mui/material";

import InsuranceClaimForm from "./components/InsuranceClaimForm";

export default function App() {
  const [files, setFiles] = useState([]);
  const [form, setForm] = useState({
    idNumber: "",
    insuredPerson: "",
    bankName: "",
    cardNumber: "",
    policyNumber: "",
    claimNumber: "",
    insuredName: "",
    insuranceSubject: [],
    coveragePeriod: "",
    incidentDate: "",
    incidentLocation: "",
    reportTime: "",
    inspectionTime: "",
    inspectionMethod: "现场查勘",
    estimatedLoss: "",
    incidentCause: "",
    remarks: "",
    phone: "",
  });

  const [loading, setLoading] = useState(false);
  const [previewImages, setPreviewImages] = useState([]);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewSrc, setPreviewSrc] = useState("");

  // 文件处理
  const handleFileChange = (e) => {
    const newFiles = Array.from(e.target.files);
    if (newFiles.length === 0) return;

    const filtered = newFiles.filter(
      (f) => !files.some((e) => e.name === f.name && e.size === f.size)
    );
    setFiles((prev) => [...prev, ...filtered]);

    const newPreviews = filtered.map((file) => ({
      name: file.name,
      url: URL.createObjectURL(file),
    }));
    setPreviewImages((prev) => [...prev, ...newPreviews]);

    e.target.value = null;
  };

  // 打开图片预览
  const handleOpenPreview = (src) => {
    setPreviewSrc(src);
    setPreviewOpen(true);
  };

  // 关闭图片预览
  const handleClosePreview = () => {
    setPreviewOpen(false);
    setPreviewSrc("");
  };

  // OCR 识别
  const parseImages = async () => {
    if (files.length === 0) return alert("请上传图片");

    const formData = new FormData();
    files.forEach((file) => formData.append("files", file));

    setLoading(true);
    try {
      const res = await fetch("http://localhost:8011/parse-docs", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error("解析失败");
      const data = await res.json();

      console.log("OCR 结果:", data);
      console.log(
        "识别的文件:",
        files.map((f) => f.name)
      );

      setForm((prev) => ({
        ...prev,
        idNumber: data.idNumber || prev.idNumber,
        insuredPerson: data.insuredPerson || prev.insuredPerson,
        bankName: data.bankName || prev.bankName,
        cardNumber: data.cardNumber || prev.cardNumber,
        // 系统截图信息
        policyNumber: data.policyNumber || prev.policyNumber,
        claimNumber: data.claimNumber || prev.claimNumber,
        insuredName: data.insuredName || prev.insuredName,
        insuranceSubject: Array.isArray(data.insuranceSubject)
          ? data.insuranceSubject
          : data.insuranceSubject
          ? [data.insuranceSubject]
          : prev.insuranceSubject,
        coveragePeriod: data.coveragePeriod || prev.coveragePeriod,
        incidentDate: data.incidentDate || prev.incidentDate,
        incidentLocation: data.incidentLocation || prev.incidentLocation,
        reportTime: data.reportTime || prev.reportTime,
        inspectionTime: data.inspectionTime || prev.inspectionTime,
        inspectionMethod: data.inspectionMethod || prev.inspectionMethod,
        estimatedLoss: data.estimatedLoss || prev.estimatedLoss,
        incidentCause: data.incidentCause || prev.incidentCause,
        remarks: data.remarks || prev.remarks,
        phone: data.phone || prev.phone,
      }));
    } catch (err) {
      console.error(err);
      alert("识别失败");
    } finally {
      setLoading(false);
    }
  };

  // 生成 Word 文档
  const generateWordDocument = () => {
    if (window.confirm("确认生成赔案处理单 Word？此操作不可逆，是否继续？")) {
      console.log("生成 Word 文件...");
      alert("赔案处理单已生成！");
    } else {
      console.log("用户取消生成");
    }
  };

  return (
    // ✅ 使用 Box 实现全屏宽度
    <Box
      sx={{
        width: "100vw",
        maxWidth: "100%",
        py: 3,
        px: { xs: 2, sm: 3, md: 4 },
        boxSizing: "border-box",
        backgroundColor: "#f4f6f8",
      }}
    >
      {/* 主布局：左侧 80% + 右侧 20% */}

      <Grid
        container
        spacing={3}
        sx={{
          width: "100%",
          ml: 0,
          boxSizing: "border-box",
        }}
      >
        {/* 左侧：表单（80%） */}
        <Grid
          item
          xs={12}
          sm={12}
          md={10}
          lg="9.6"
          sx={{
            flexShrink: 0,
            flexGrow: 1,
            minWidth: 0,
          }}
        >
          <InsuranceClaimForm formData={form} />
        </Grid>

        <Grid
          item
          xs={12}
          sm={12}
          md={2}
          lg="2.4"
          sx={{
            flexShrink: 0,
            flexGrow: 0,
            display: "flex",
            flexDirection: "row",
          }}
        >
          <Paper
            sx={{
              p: 3,
              borderRadius: "12px",
              border: "1px solid #e0e0e0",
              boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
              backgroundColor: "#fff",
              display: "flex",
              flexDirection: "column",
            }}
          >
            <Typography variant="h6" color="textSecondary" gutterBottom>
              📎 上传材料
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              请上传身份证、银行卡、系统截图等
            </Typography>
            <Typography
              variant="caption"
              color="textSecondary"
              sx={{ mb: 1, display: "block" }}
            >
              当前文件数量: {files.length}
            </Typography>

            {/* 选择图片按钮 */}
            <Button
              component="label"
              variant="outlined"
              startIcon="📁"
              fullWidth
              sx={{
                mb: 2,
                borderColor: "#1976d2",
                color: "#1976d2",
                "&:hover": {
                  backgroundColor: "rgba(25, 118, 210, 0.08)",
                },
              }}
            >
              选择图片
              <input
                type="file"
                multiple
                accept="image/*"
                hidden
                onChange={handleFileChange}
              />
            </Button>

            {/* 图片预览区域：固定高度 + 滚动 */}
            <Box
              sx={{
                flex: 1,
                maxHeight: "400px",
                overflowY: "auto",
                mt: 1,
                px: 0.5,
                "&::-webkit-scrollbar": {
                  width: "6px",
                },
                "&::-webkit-scrollbar-thumb": {
                  backgroundColor: "#b0b0b0",
                  borderRadius: "3px",
                },
              }}
            >
              {previewImages.length === 0 ? (
                <Typography
                  variant="body2"
                  color="textSecondary"
                  textAlign="center"
                  py={2}
                >
                  暂无图片
                </Typography>
              ) : (
                <Grid container spacing={1}>
                  {previewImages.map((img, i) => (
                    <Grid item xs={12} key={i}>
                      <Box
                        sx={{
                          position: "relative",
                          display: "inline-block",
                          width: "100%",
                          height: 90,
                          borderRadius: "8px",
                          overflow: "hidden",
                          backgroundColor: "#f5f5f5",
                          border: "1px solid #ddd",
                        }}
                      >
                        {/* 缩略图 - 点击放大 */}
                        <Box
                          component="img"
                          src={img.url}
                          alt={img.name}
                          onClick={() => handleOpenPreview(img.url)}
                          sx={{
                            width: "100%",
                            height: "100%",
                            objectFit: "cover",
                            cursor: "pointer",
                            display: "flex",
                            flexDirection: "row",

                            transition: "transform 0.2s",
                            "&:hover": {
                              transform: "scale(1.02)",
                            },
                          }}
                        />

                        {/* 删除按钮 */}
                        <Box
                          component="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            // 清理要删除的图片URL
                            URL.revokeObjectURL(previewImages[i].url);
                            // 同时删除预览图片和对应的文件
                            setPreviewImages((prev) =>
                              prev.filter((_, idx) => idx !== i)
                            );
                            setFiles((prev) =>
                              prev.filter((_, idx) => idx !== i)
                            );
                          }}
                          sx={{
                            position: "absolute",
                            top: 4,
                            right: 4,
                            width: 24,
                            height: 24,
                            borderRadius: "50%",
                            backgroundColor: "rgba(255, 0, 0, 0.7)",
                            color: "#fff",
                            border: "none",
                            fontSize: "16px",
                            fontWeight: "bold",
                            cursor: "pointer",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            padding: 0,
                            "&:hover": {
                              backgroundColor: "rgba(255, 0, 0, 0.9)",
                            },
                          }}
                        >
                          ×
                        </Box>

                        {/* 文件名 */}
                        <Typography
                          variant="caption"
                          sx={{
                            position: "absolute",
                            bottom: 0,
                            left: 0,
                            right: 0,
                            backgroundColor: "rgba(0,0,0,0.5)",
                            color: "#fff",
                            py: 0.5,
                            px: 1,
                            whiteSpace: "nowrap",
                            overflow: "hidden",
                            textOverflow: "ellipsis",
                          }}
                        >
                          {img.name}
                        </Typography>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              )}
            </Box>

            {/* 识别按钮 */}
            <Button
              fullWidth
              variant="contained"
              color="primary"
              disabled={loading || files.length === 0}
              onClick={parseImages}
              startIcon={loading ? null : "🔍"}
              sx={{ mt: 3, fontWeight: "bold", py: 1.2 }}
            >
              {loading ? (
                <CircularProgress size={20} color="inherit" />
              ) : (
                "开始识别"
              )}
            </Button>

            {/* 清除所有文件按钮 */}
            {files.length > 0 && (
              <Button
                fullWidth
                variant="outlined"
                color="secondary"
                disabled={loading}
                onClick={() => {
                  setFiles([]);
                  setPreviewImages([]);
                  // 清理URL对象，避免内存泄漏
                  previewImages.forEach((img) => URL.revokeObjectURL(img.url));
                }}
                startIcon="🗑️"
                sx={{ mt: 1, py: 1 }}
              >
                清除所有文件
              </Button>
            )}
          </Paper>
        </Grid>
      </Grid>

      {/* 生成按钮 */}
      <Box sx={{ textAlign: "center", mt: 5, mb: 3 }}>
        <Button
          variant="contained"
          color="success"
          size="large"
          onClick={generateWordDocument}
          startIcon="📄"
          sx={{
            py: 1.5,
            px: 4,
            fontSize: "16px",
            fontWeight: "bold",
            boxShadow: "0 4px 12px rgba(76, 175, 80, 0.3)",
          }}
        >
          生成赔案处理单 Word
        </Button>
      </Box>

      {/* 图片放大预览（模态层） */}
      {previewOpen && previewSrc && (
        <Box
          sx={{
            position: "fixed",
            top: 0,
            left: 0,
            width: "100vw",
            height: "100vh",
            backgroundColor: "rgba(0, 0, 0, 0.9)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1300,
            cursor: "pointer",
            animation: "fadeIn 0.3s",
          }}
          onClick={handleClosePreview}
        >
          <Box
            component="img"
            src={previewSrc}
            alt="预览"
            sx={{
              maxHeight: "90vh",
              maxWidth: "90vw",
              objectFit: "contain",
              borderRadius: "8px",
              boxShadow: "0 4px 20px rgba(255,255,255,0.2)",
              transition: "all 0.2s",
            }}
            onClick={(e) => e.stopPropagation()}
          />
        </Box>
      )}
    </Box>
  );
}
