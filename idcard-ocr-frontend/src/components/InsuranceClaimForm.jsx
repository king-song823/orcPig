// src/components/InsuranceClaimForm.jsx
import React from "react";
import { Paper, Grid, Typography, Box } from "@mui/material";

// 只读字段组件
const DisplayField = ({ label, value, minWidth }) => (
  <Box
    sx={{
      mb: 2,
    }}
  >
    {/* 标签 */}
    <Typography
      component="label"
      variant="body2"
      color="textSecondary"
      fontWeight="bold"
      sx={{
        display: "block",
        mb: 0.5,
      }}
    >
      {label}
    </Typography>

    {/* 值显示区：设置最小宽度 */}
    <Typography
      variant="body1"
      sx={{
        p: 1.5,
        borderRadius: "8px",
        backgroundColor: "#f9f9f9",
        border: "1px solid #e0e0e0",
        minHeight: "36px",
        display: "flex",
        alignItems: "center",
        wordBreak: "break-word",
        fontSize: "14px",
        lineHeight: 1,
        color: "text.primary",
        minWidth: minWidth ? minWidth : "auto", // ✅ 最小宽度控制
      }}
    >
      {value || "—"}
    </Typography>
  </Box>
);

const InsuranceClaimForm = ({ formData }) => {
  return (
    <Paper
      sx={{
        p: { xs: 3, sm: 4 },
        borderRadius: "12px",
        maxWidth: "100%",
        marginX: "auto",
        border: "1px solid #e0e0e0",
        boxShadow: "0 4px 12px rgba(0,0,0,0.08)",
      }}
    >
      <Box
        sx={{
          mb: 2,
        }}
      >
        {/* 标题 */}
        <Typography
          variant="h5"
          align="center"
          gutterBottom
          fontWeight="bold"
          color="#1976d2"
          sx={{
            fontSize: { xs: "1.5rem", sm: "1.75rem" },
            textAlign: { xs: "left", sm: "center" },
          }}
        >
          养殖业保险简易赔案处理单
        </Typography>

        {/* 案件基本信息 */}
        <Typography
          variant="h6"
          gutterBottom
          fontWeight="bold"
          color="#1976d2"
          sx={{ mt: 2 }}
        >
          案件基本信息
        </Typography>
        <Grid
          container
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(3, 1fr)",
            },
            gap: 4,
          }}
        >
          <Grid item>
            <DisplayField label="保单号" value={formData.policyNumber} />
          </Grid>
          <Grid item>
            <DisplayField label="报案号" value={formData.claimNumber} />
          </Grid>
          <Grid item>
            <DisplayField label="被保险人" value={formData.insuredPerson} />
          </Grid>
        </Grid>
        <Grid
          container
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(3, 1fr)",
            },
            gap: 4,
          }}
        >
          <Grid item>
            <DisplayField
              label="保险标的"
              value={
                Array.isArray(formData.insuranceSubject) &&
                formData.insuranceSubject.length
                  ? formData.insuranceSubject.join("、")
                  : formData.insuranceSubject || ""
              }
            />
          </Grid>
          <Grid item>
            <DisplayField label="保险期间" value={formData.coveragePeriod} />
          </Grid>
          <Grid item>
            <DisplayField label="出险日期" value={formData.reportTime} />
          </Grid>
        </Grid>
        <Grid
          container
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(3, 1fr)",
            },
            gap: 4,
          }}
        >
          <Grid item>
            <DisplayField label="出险地点" value={formData.incidentLocation} />
          </Grid>
          <Grid item>
            <DisplayField label="报案时间" value={formData.reportTime} />
          </Grid>
        </Grid>

        {/* 查勘详情 */}
        <Typography
          variant="h6"
          gutterBottom
          fontWeight="bold"
          color="#1976d2"
          sx={{ mt: 3 }}
        >
          查勘定损情况
        </Typography>
        <Grid
          container
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(3, 1fr)",
            },
            gap: 4,
          }}
        >
          <Grid item>
            <DisplayField label="查勘时间" value={formData.inspectionTime} />
          </Grid>
          <Grid item>
            <DisplayField label="查勘方式" value={formData.inspectionMethod} />
          </Grid>
        </Grid>
        {/* 出险原因及经过 */}
        <Typography
          variant="h6"
          gutterBottom
          fontWeight="bold"
          color="#1976d2"
          sx={{ mt: 3 }}
        >
          出险原因及经过
        </Typography>
        <Typography
          component="span"
          variant="body1"
          sx={{
            display: "inline",
            fontSize: "14px",
            lineHeight: 1.7,
          }}
        >
          <strong>
            {formData.inspectionTime
              ? formData.inspectionTime
              : "___年___月___日"}
          </strong>
          ，被保险人饲养的
          <strong>___只/头</strong>
          标的死亡，
          {/* 中屏及以上显示换行 */}
          <Box
            component="span"
            sx={{ display: { xs: "inline", sm: "inline", md: "block" } }}
          >
            {" "}
          </Box>
          报案后我司查勘人员协同畜牧兽医站工作人员到现场查勘。
          {/* 小屏显示换行 */}
          <Box
            component="span"
            sx={{ display: { xs: "block", sm: "block", md: "inline" } }}
          >
            {" "}
          </Box>
          经兽医对标的死亡原因进行诊断，该标的是因
          <strong>
            {formData.incidentCause ? formData.incidentCause : "___________"}
          </strong>
          导致死亡。
        </Typography>
        {/* 赔款支付信息 */}
        <Typography
          variant="h6"
          gutterBottom
          fontWeight="bold"
          color="#1976d2"
          sx={{ mt: 3 }}
        >
          赔款支付信息
        </Typography>
        <Grid
          container
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(3, 1fr)",
            },
            gap: 4,
          }}
        >
          <Grid item>
            <DisplayField label="户名" value={formData.insuredPerson} />
          </Grid>
          <Grid item>
            <DisplayField label="身份证号" value={formData.idNumber} />
          </Grid>
          <Grid item>
            <DisplayField label="开户行" value={formData.bankName} />
          </Grid>
        </Grid>
        <Grid
          container
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(3, 1fr)",
            },
            gap: 4,
          }}
        >
          <Grid item>
            <DisplayField label="银行账号" value={formData.cardNumber} />
          </Grid>
          <Grid item>
            <DisplayField label="联系电话" value={formData.phone} />
          </Grid>
        </Grid>

        {/* 防疫核实 */}
        <Typography
          variant="h6"
          gutterBottom
          fontWeight="bold"
          color="#1976d2"
          sx={{ mt: 3 }}
        >
          防疫及死亡原因核实情况
        </Typography>
        <Grid
          container
          sx={{
            display: "grid",
            gridTemplateColumns: {
              xs: "1fr",
              sm: "repeat(2, 1fr)",
              md: "repeat(3, 1fr)",
            },
            gap: 4,
          }}
        >
          <Grid item>
            <DisplayField label="被保险人" value={formData.insuredPerson} />
          </Grid>
          <Grid item>
            <DisplayField
              label="估损金额（元）"
              value={formData.estimatedLoss}
            />
          </Grid>
          <Grid item>
            <DisplayField label="出险原因" value={formData.incidentCause} />
          </Grid>
        </Grid>
      </Box>
    </Paper>
  );
};

export default InsuranceClaimForm;
