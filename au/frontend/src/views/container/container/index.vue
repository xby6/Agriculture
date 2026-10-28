<template>
  <div class="app-container agri-business-page">
    <AgriPageHeader
      title="农业算法与模型服务中心"
      eyebrow="MODEL SERVICE CENTER"
      icon="Cpu"
      description="统一管理病害图像检测、病情指数预测、长势评估和报告生成服务，支持模型版本维护、算法接入与服务状态查看。"
    />
    <el-form :model="queryParams" ref="queryRef" :inline="true" v-show="showSearch" label-width="68px">
      <el-form-item label="服务名称" prop="name">
        <el-input
          v-model="queryParams.name"
          placeholder="请输入服务名称"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item label="服务类型" prop="type">
        <el-input
          v-model="queryParams.type"
          placeholder="请输入服务类型"
          clearable
          style="width: 240px"
          @keyup.enter="handleQuery"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" icon="Search" @click="handleQuery">搜索</el-button>
        <el-button icon="Refresh" @click="resetQuery">重置</el-button>
      </el-form-item>
    </el-form>

    <el-row :gutter="10" class="mb8">
      <el-col :span="1.5">
        <el-button
          type="primary"
          plain
          icon="Plus"
          @click="handleAdd"
          v-hasPermi="['container:container:add']"
        >新增</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="success"
          plain
          icon="Edit"
          :disabled="single"
          @click="handleUpdate"
          v-hasPermi="['container:container:edit']"
        >修改</el-button>
      </el-col>
      <el-col :span="1.5">
        <el-button
          type="danger"
          plain
          icon="Delete"
          :disabled="multiple"
          @click="handleDelete"
          v-hasPermi="['container:container:remove']"
        >删除</el-button>
      </el-col>
      <el-col :span="1.5">
      </el-col>
      <right-toolbar v-model:showSearch="showSearch" @queryTable="getList"></right-toolbar>
    </el-row>

    <el-table v-loading="loading" :data="containerList" @selection-change="handleSelectionChange">
      <el-table-column type="selection" width="55" align="center" />
      <el-table-column label="服务标识" align="center" prop="id" />
      <el-table-column label="服务名称" align="center" prop="name" />
      <el-table-column label="服务地址" align="center" prop="url" />
      <el-table-column label="服务类型" align="center" prop="type" />
      <el-table-column label="创建时间" align="center" prop="create_time" width="180">
        <template #default="scope">
          <span>{{ parseTime(scope.row.create_time, '{y}-{m}-{d}') }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" align="center" class-name="small-padding fixed-width">
        <template #default="scope">
          <el-button link type="primary" icon="View" @click="handleView(scope.row)">查看</el-button>
          <el-button link type="primary" icon="Edit" @click="handleUpdate(scope.row)" v-hasPermi="['container:container:edit']">修改</el-button>
          <el-button link type="primary" icon="Delete" @click="handleDelete(scope.row)" v-hasPermi="['container:container:remove']">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    

    <pagination
      v-show="total>0"
      :total="total"
      v-model:page="queryParams.pageNum"
      v-model:limit="queryParams.pageSize"
      @pagination="getList"
    />

    <!-- 添加或修改算法服务对话框 -->
    <el-dialog :title="title" v-model="open" width="500px" append-to-body>
      <el-form ref="containerRef" :model="form" :rules="rules" label-width="80px">
      <el-form-item v-if="renderField(true, true)" label="服务名称" prop="name">
        <el-input v-model="form.name" placeholder="请输入服务名称" />
      </el-form-item>
      <el-form-item v-if="renderField(true, true)" label="服务地址" prop="url">
        <el-input v-model="form.url" placeholder="请输入服务地址" />
      </el-form-item>
      <el-form-item v-if="renderField(true, true)" label="服务类型" prop="type">
        <el-input v-model="form.type" placeholder="请输入服务类型" />
      </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button type="primary" @click="submitForm">确 定</el-button>
          <el-button @click="cancel">取 消</el-button>
        </div>
      </template>
    </el-dialog>

     <!-- 查看容器模型与算法对话框 -->
    <el-dialog title="农业模型与算法管理" v-model="viewOpen" width="800px">
        <AlgorithmManagement :container-id="currentContainerId" />
        <ModelManagement :container-id="currentContainerId"/>
    </el-dialog>
    </div>

 
</template>

<script setup name="AgricultureModelCenter">
import AgriPageHeader from '@/components/AgriPageHeader'
import { listContainer, getContainer, delContainer, addContainer, updateContainer, } from "@/api/container/container";
import AlgorithmManagement from './AlgorithmManagement.vue'
import ModelManagement from './ModelManagement.vue'

const { proxy } = getCurrentInstance();

const containerList = ref([]);
const open = ref(false);
const open2 = ref(false);
const loading = ref(true);
const showSearch = ref(true);
const ids = ref([]);
const single = ref(true);
const multiple = ref(true);
const total = ref(0);
const title = ref("");
const viewOpen = ref(false);
const modelData = ref([]); 
const currentContainerId = ref(null);
const data = reactive({
  form: {},
  queryParams: {
    pageNum: 1,
    pageSize: 10,
    name: null,
    type: null,

  },
  rules: {
    name: [
      { required: true, message: "服务名称不能为空", trigger: "blur" }
    ],
    url: [
      { required: true, message: "服务地址不能为空", trigger: "blur" }
    ],
  }
});

const { queryParams, form, rules } = toRefs(data);

 function handleView(row) {
      currentContainerId.value = row.id; 
      viewOpen.value = true;
    }

/** 查询模型服务列表 */
function getList() {
  loading.value = true;
  listContainer(queryParams.value).then(response => {
    containerList.value = response.rows;
    modelData.value=response.rows;
    total.value = response.total;
    loading.value = false;
  });
}

/** 取消按钮 */
function cancel() {
  open.value = false;
  open2.value=false;
  reset();
}

/** 表单重置 */
function reset() {
  form.value = {
    id: null,
    name: null,
    url: null,
    type: null,
    create_time: null,
    dept: null,
  };
  proxy.resetForm("containerRef");
}

/** 搜索按钮操作 */
function handleQuery() {
  queryParams.value.pageNum = 1;
  getList();
}

/** 重置按钮操作 */
function resetQuery() {
  proxy.resetForm("queryRef");
  handleQuery();
}

/** 多选框选中数据  */
function handleSelectionChange(selection) {
  ids.value = selection.map(item => item.id);
  single.value = selection.length != 1;
  multiple.value = !selection.length;
}

/** 新增按钮操作 */
function handleAdd() {
  reset();
  open.value = true;
  title.value = "新增模型服务";
}

/** 修改按钮操作 */
function handleUpdate(row) {
  reset();
  const _id = row.id || ids.value;
  getContainer(_id).then(response => {
    form.value = response.data;
    open.value = true;
    title.value = "修改模型服务";
  });
}

/** 提交按钮 */
function submitForm() {
  proxy.$refs["containerRef"].validate(valid => {
    if (valid) {
      if (form.value.id != null) {
        updateContainer(form.value).then(response => {
          proxy.$modal.msgSuccess("修改成功");
          open.value = false;
          getList();
        });
      } else {
        addContainer(form.value).then(response => {
          proxy.$modal.msgSuccess("新增成功");
          open.value = false;
          getList();
        });
      }
    }
  });
}

/** 删除按钮操作 */
function handleDelete(row) {
  const _ids = row.id || ids.value;
  proxy.$modal.confirm('是否确认删除模型服务编号为"' + _ids + '"的数据项？').then(function() {
    return delContainer(_ids);
  }).then(() => {
    getList();
    proxy.$modal.msgSuccess("删除成功");
  }).catch(() => {});
}


/** 是否渲染字段 */
function renderField(insert, edit) {
  return form.value.id == null ? insert : edit;
}

getList();
</script>
<style>
.management-container {
  display: flex;
  justify-content: space-between;
  min-height: 25vh;
  padding: 20px;
  gap: 20px;
}

.agri-business-page { min-height: calc(100vh - 84px); background:#061323; }
</style>